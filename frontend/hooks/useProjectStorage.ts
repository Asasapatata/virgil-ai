// hooks/useProjectStorage.ts - Interfaccia Project aggiornata
import { useState, useEffect, useCallback } from 'react';

// Interfaccia Project estesa
export interface Project {
  project_id: string;
  project_name: string;
  status: string; // 'created', 'processing', 'generating_code', 'generating_tests', 'running_tests', 'completed', 'failed', 'error', 'uploaded', 'imported'
  created_at: string;
  description?: string;
  updated_at?: string;
  current_iteration?: number;
  test_results?: {
    success: boolean;
    frontend?: { success: boolean; logs?: string };
    backend?: { success: boolean; logs?: string };
    e2e?: { success: boolean; logs?: string };
  };
  has_final?: boolean;
  
  // Campi per Stop Generation
  stopped_by_user?: boolean;
  stopped_at?: string;
  
  // Campi per progetti importati
  imported?: boolean;
  imported_files?: string[];
  analysis?: {
    technologies?: string[];
    estimated_complexity?: 'low' | 'medium' | 'high';
    suggestions?: string[];
  };
  
  // Campi per progetti modificati
  modification_id?: string;
  modification_mode?: 'incremental' | 'complete_rewrite';
}

// Usa la tua implementazione esistente di useProjectStorage
// Aggiungo solo l'interfaccia estesa per supportare le nuove funzionalità