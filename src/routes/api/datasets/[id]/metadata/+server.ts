// src/routes/api/datasets/[id]/metadata/+server.ts
import { json, error } from '@sveltejs/kit';
import { datasets } from '$lib/data/datasets.js';
import type { RequestHandler } from './$types.js';
import { readFileSync, statSync } from 'fs';
import { createHash } from 'crypto';
import path from 'path';

export const GET: RequestHandler = async ({ params }) => {
  const { id } = params;
  
  // Find the dataset
  const dataset = datasets.find(d => d.id === id);
  if (!dataset) {
    error(404, { message: 'Dataset not found' });
  }

  // Only handle local files for now
  if (!dataset.url.startsWith('/')) {
    error(400, { message: 'Metadata only available for local datasets' });
  }

  try {
    // Construct the file path (remove leading slash and prepend static)
    const filePath = path.join('static', dataset.url);
    
    // Get file stats
    const stats = statSync(filePath);
    
    // Read file to generate etag
    const fileContent = readFileSync(filePath);
    const etag = createHash('md5').update(fileContent).digest('hex');
    
    return json({
      id: dataset.id,
      name: dataset.name,
      description: dataset.description,
      url: dataset.url,
      status: 'available',
      lastModified: stats.mtime.toISOString(),
      fileSize: stats.size,
      contentType: dataset.contentType || 'application/octet-stream',
      etag,
      checkedAt: new Date().toISOString()
    });
    
  } catch (err) {
    console.error(`Error reading file for dataset ${id}:`, err);
    
    return json({
      id: dataset.id,
      name: dataset.name,
      description: dataset.description,
      url: dataset.url,
      status: 'unavailable',
      error: 'File not accessible',
      checkedAt: new Date().toISOString()
    }, { status: 503 });
  }
};