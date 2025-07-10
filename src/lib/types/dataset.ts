// src/lib/types/dataset.ts

export type DatasetStatus = 'available' | 'unavailable' | 'checking' | 'unknown';

export interface Dataset {
  id: string;
  name: string;
  description: string;
  url: string;
  source: string; // e.g., "GitHub", "Kaggle", "API endpoint"
  tags: string[];
  lastChecked?: Date;
  status: DatasetStatus;
  responseTime?: number; // in milliseconds
  // Metadata for external tools like Dagster
  fileSize?: number; // in bytes
  lastModified?: Date;
  contentType?: string;
  etag?: string; // for caching/change detection
}

export interface DatasetCheckResult {
  id: string;
  status: DatasetStatus;
  responseTime?: number;
  error?: string;
  checkedAt: Date;
}

// Specific dataset schemas
export interface UVMProfessor {
  payroll_name: string;
  position: string;
  oa_display_name: string;
  is_prof: boolean;
  perceived_as_male: boolean;
  host_dept: string;
  has_research_group: boolean;
  group_size: number;
  oa_uid: string;
  group_url: string;
  first_pub_year: number;
  notes: string;
}

// API response types
export interface DatasetMetadataResponse {
  id: string;
  name: string;
  description: string;
  url: string;
  status: DatasetStatus;
  lastModified?: string;
  fileSize?: number;
  contentType?: string;
  etag?: string;
  checkedAt: string;
  error?: string;
}