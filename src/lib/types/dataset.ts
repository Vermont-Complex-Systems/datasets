// src/lib/types/dataset.ts

export interface Dataset {
  id: string;
  name: string;
  description: string;
  url: string;
  display: string;
  source: string;
  keywords: string[];
  contentType: string;
  format: 'CSV' | 'JSON' | 'TSV' | 'XLSX';
  size?: string; // Human readable size like "48KB"
  lastUpdated?: string; // ISO date string
}

// Specific dataset schemas for type safety
export interface ResearchGroups {
  payroll_name: string;
  payroll_year: number;
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
  inst_ipeds_id: number;
  notes: string;
}

export interface Deparment {
  department: string;
  college: string;
  category: string;
  year: number;
  inst_ipeds_id: number;
}