import { useState, useEffect, useCallback } from 'react';
import { Project } from './useProjectStorage';

const STORAGE_KEY = 'ai_code_generator_projects';
const MAX_PROJECTS = 200;
const MAX_STORAGE_SIZE = 8 * 1024 * 1024; // 8MB
const ACTIVE_PROJECTS_KEY = 'ai_code_generator_active_projects';

interface StorageMetrics {
  projectCount: number;
  storageSize: number;
  lastCleanup: Date | null;
  errors: string[];
}

export const useRobustStorage = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [metrics, setMetrics] = useState<StorageMetrics>({
    projectCount: 0,
    storageSize: 0,
    lastCleanup: null,
    errors: []
  });
  const [isStorageAvailable, setIsStorageAvailable] = useState(true);

  // Check if localStorage is available
  const checkStorageAvailability = useCallback(() => {
    try {
      const test = '__storage_test__';
      localStorage.setItem(test, test);
      localStorage.removeItem(test);
      setIsStorageAvailable(true);
      return true;
    } catch (error) {
      setIsStorageAvailable(false);
      console.warn('LocalStorage not available:', error);
      return false;
    }
  }, []);

  // Calculate storage size
  const calculateStorageSize = useCallback(() => {
    if (!isStorageAvailable) return 0;
    
    try {
      let totalSize = 0;
      for (let key in localStorage) {
        if (localStorage.hasOwnProperty(key)) {
          totalSize += localStorage.getItem(key)?.length || 0;
        }
      }
      return totalSize;
    } catch (error) {
      console.warn('Error calculating storage size:', error);
      return 0;
    }
  }, [isStorageAvailable]);

  // Load projects with error handling
  const loadProjects = useCallback(() => {
    if (!checkStorageAvailability()) {
      setProjects([]);
      return;
    }

    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (!stored) {
        setProjects([]);
        return;
      }

      const parsed = JSON.parse(stored);
      if (!Array.isArray(parsed)) {
        throw new Error('Invalid projects data format');
      }

      // Validate each project
      const validProjects = parsed.filter((project: any) => {
        return (
          project &&
          typeof project === 'object' &&
          project.project_id &&
          project.project_name &&
          project.created_at
        );
      });

      setProjects(validProjects);
      setMetrics(prev => ({
        ...prev,
        projectCount: validProjects.length,
        storageSize: calculateStorageSize()
      }));

    } catch (error) {
      console.error('Error loading projects:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      setMetrics(prev => ({
        ...prev,
        errors: [...prev.errors, `Load error: ${errorMessage}`]
      }));
      
      // Try to recover by clearing corrupted data
      try {
        localStorage.removeItem(STORAGE_KEY);
        setProjects([]);
      } catch (clearError) {
        console.error('Error clearing corrupted data:', clearError);
      }
    }
  }, [checkStorageAvailability, calculateStorageSize]);

  // Save projects with cleanup and validation
  const saveProjects = useCallback((newProjects: Project[]) => {
    if (!isStorageAvailable) {
      setMetrics(prev => ({
        ...prev,
        errors: [...prev.errors, 'Storage not available']
      }));
      return false;
    }

    try {
      // Sort by date (newest first)
      const sortedProjects = [...newProjects].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );

      // Limit number of projects
      const limitedProjects = sortedProjects.slice(0, MAX_PROJECTS);

      // Check if we need to cleanup due to size
      const dataString = JSON.stringify(limitedProjects);
      if (dataString.length > MAX_STORAGE_SIZE / 2) {
        // Keep only recent projects if size is too large
        const recentProjects = limitedProjects.slice(0, Math.floor(MAX_PROJECTS / 2));
        localStorage.setItem(STORAGE_KEY, JSON.stringify(recentProjects));
        setProjects(recentProjects);
        
        setMetrics(prev => ({
          ...prev,
          lastCleanup: new Date(),
          projectCount: recentProjects.length,
          storageSize: calculateStorageSize(),
          errors: [...prev.errors, 'Auto-cleanup performed due to size limit']
        }));
      } else {
        localStorage.setItem(STORAGE_KEY, dataString);
        setProjects(limitedProjects);
        
        setMetrics(prev => ({
          ...prev,
          projectCount: limitedProjects.length,
          storageSize: calculateStorageSize()
        }));
      }

      return true;
    } catch (error) {
      console.error('Error saving projects:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      setMetrics(prev => ({
        ...prev,
        errors: [...prev.errors, `Save error: ${errorMessage}`]
      }));

      // Handle quota exceeded error
      if (error instanceof Error && error.name === 'QuotaExceededError') {
        try {
          // Emergency cleanup - keep only last 50 projects
          const emergencyProjects = newProjects.slice(0, 50);
          localStorage.setItem(STORAGE_KEY, JSON.stringify(emergencyProjects));
          setProjects(emergencyProjects);
          
          setMetrics(prev => ({
            ...prev,
            lastCleanup: new Date(),
            projectCount: emergencyProjects.length,
            errors: [...prev.errors, 'Emergency cleanup performed - storage quota exceeded']
          }));
          
          return true;
        } catch (emergencyError) {
          console.error('Emergency cleanup failed:', emergencyError);
          return false;
        }
      }

      return false;
    }
  }, [isStorageAvailable, calculateStorageSize]);

  // Initialize on mount
  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  

// Aggiungere queste funzioni a useRobustStorage
// Funzione per aggiungere un progetto all'elenco di quelli attivi
const trackActiveProject = useCallback((projectId: string) => {
  if (!isStorageAvailable) return false;
  
  try {
    // Ottieni la lista dei progetti attivi
    const activeProjectsStr = localStorage.getItem(ACTIVE_PROJECTS_KEY);
    const activeProjects = activeProjectsStr ? JSON.parse(activeProjectsStr) : [];
    
    // Aggiungi se non esiste già
    if (!activeProjects.includes(projectId)) {
      activeProjects.push(projectId);
      localStorage.setItem(ACTIVE_PROJECTS_KEY, JSON.stringify(activeProjects));
      console.log(`Progetto ${projectId} aggiunto alla lista dei progetti attivi`);
    }
    
    return true;
  } catch (error) {
    console.error('Errore nel tracciamento del progetto attivo:', error);
    return false;
  }
}, [isStorageAvailable]);

// Funzione per rimuovere un progetto dall'elenco di quelli attivi
const untrackActiveProject = useCallback((projectId: string) => {
  if (!isStorageAvailable) return false;
  
  try {
    const activeProjectsStr = localStorage.getItem(ACTIVE_PROJECTS_KEY);
    if (!activeProjectsStr) return true;
    
    const activeProjects = JSON.parse(activeProjectsStr);
    const updatedActiveProjects = activeProjects.filter((id: string) => id !== projectId);
    
    localStorage.setItem(ACTIVE_PROJECTS_KEY, JSON.stringify(updatedActiveProjects));
    console.log(`Progetto ${projectId} rimosso dalla lista dei progetti attivi`);
    
    return true;
  } catch (error) {
    console.error('Errore nella rimozione del progetto attivo:', error);
    return false;
  }
}, [isStorageAvailable]);
const getActiveProjects = useCallback(() => {
  if (!isStorageAvailable) return [];
  
  try {
    const activeProjectsStr = localStorage.getItem('active_projects');
    return activeProjectsStr ? JSON.parse(activeProjectsStr) : [];
  } catch (error) {
    console.error('Error getting active projects:', error);
    return [];
  }
}, [isStorageAvailable]);


  const updateProject = useCallback((projectId: string, updates: Partial<Project>) => {
    const updatedProjects = projects.map(p =>
      p.project_id === projectId
        ? { ...p, ...updates, updated_at: new Date().toISOString() }
        : p
    );
    saveProjects(updatedProjects);
  }, [projects, saveProjects]);

  const removeProject = useCallback((projectId: string) => {
    const updatedProjects = projects.filter(p => p.project_id !== projectId);
    saveProjects(updatedProjects);
  }, [projects, saveProjects]);

  const getProject = useCallback((projectId: string) => {
    return projects.find(p => p.project_id === projectId);
  }, [projects]);

  // Maintenance functions
  const forceCleanup = useCallback(() => {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - 30); // Keep last 30 days

    const recentProjects = projects.filter(p => 
      new Date(p.created_at) > cutoffDate
    ).slice(0, 100); // Max 100 projects

    saveProjects(recentProjects);
    
    return {
      removed: projects.length - recentProjects.length,
      remaining: recentProjects.length
    };
  }, [projects, saveProjects]);

  const clearAllProjects = useCallback(() => {
    try {
      localStorage.removeItem(STORAGE_KEY);
      setProjects([]);
      setMetrics(prev => ({
        ...prev,
        projectCount: 0,
        storageSize: calculateStorageSize(),
        lastCleanup: new Date()
      }));
      return true;
    } catch (error) {
      console.error('Error clearing projects:', error);
      return false;
    }
  }, [calculateStorageSize]);

  const exportProjects = useCallback(() => {
    try {
      const exportData = {
        projects,
        exportDate: new Date().toISOString(),
        version: '1.0'
      };
      
      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: 'application/json'
      });
      
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ai-code-generator-projects-${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      return true;
    } catch (error) {
      console.error('Error exporting projects:', error);
      return false;
    }
  }, [projects]);

  const importProjects = useCallback((file: File): Promise<{ success: boolean; count?: number; error?: string }> => {
    return new Promise((resolve) => {
      const reader = new FileReader();
      
      reader.onload = (event) => {
        try {
          const importData = JSON.parse(event.target?.result as string);
          
          if (!importData.projects || !Array.isArray(importData.projects)) {
            resolve({ success: false, error: 'Invalid import format' });
            return;
          }
          
          // Merge with existing projects (avoid duplicates)
          const existingIds = new Set(projects.map(p => p.project_id));
          const newProjects = importData.projects.filter(
            (p: Project) => !existingIds.has(p.project_id)
          );
          
          const mergedProjects = [...projects, ...newProjects];
          const success = saveProjects(mergedProjects);
          
          resolve({ 
            success, 
            count: success ? newProjects.length : 0,
            error: success ? undefined : `Failed to save imported projects`
          });
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to parse import file';
          resolve({ success: false, error: errorMessage });
        }
      };
      
      reader.onerror = () => {
        resolve({ success: false, error: 'Failed to read file' });
      };
      
      reader.readAsText(file);
    });
  }, [projects, saveProjects]);

  // Clear errors
  const clearErrors = useCallback(() => {
    setMetrics(prev => ({ ...prev, errors: [] }));
  }, []);

  // Project management functions
  const addProject = useCallback((project: Project) => {
  // Logging e validazione
  console.log('Adding project to storage:', project);
  
  // Validazione dei campi essenziali
  if (!project.project_id || !project.project_name || !project.created_at) {
    console.error('Invalid project data, missing required fields:', project);
    setMetrics(prev => ({
      ...prev,
      errors: [...prev.errors, `Add error: Invalid project data, missing required fields`]
    }));
    return false;
  }
  
  // Verifica che il progetto non esista già
  const existingProject = projects.find(p => p.project_id === project.project_id);
  if (existingProject) {
    console.log('Project already exists, updating instead:', project);
    return updateProject(project.project_id, project);
  }

  // Garantisce che il progetto abbia tutti i campi necessari
  const normalizedProject: Project = {
    ...project,
    status: project.status || 'created',
    created_at: project.created_at,
    updated_at: project.updated_at || new Date().toISOString()
  };
  
  // Aggiunta immutabile
  const updatedProjects = [normalizedProject, ...projects];
  
  // Salvataggio con doppia verifica
  const saveResult = saveProjects(updatedProjects);
  
  // Verifica che il salvataggio sia avvenuto correttamente
  if (saveResult) {
    // Verifica che il progetto sia stato effettivamente salvato
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        const savedProject = parsed.find((p: Project) => p.project_id === project.project_id);
        if (!savedProject) {
          console.error('Project was not saved correctly:', project);
          setMetrics(prev => ({
            ...prev,
            errors: [...prev.errors, `Add error: Project was not saved correctly`]
          }));
          
          // Forza un nuovo salvataggio
          localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedProjects));
        }
      }
    } catch (error) {
      console.error('Error verifying project save:', error);
    }
  }
  
  return saveResult;
}, [projects, saveProjects, updateProject]);

const syncActiveProjects = useCallback(async (api: any) => {
  const activeProjectIds = getActiveProjects();
  let syncedCount = 0;
  
  for (const projectId of activeProjectIds) {
    // Verifica se il progetto è già nella lista
    const existingProject = getProject(projectId);
    if (!existingProject) {
      try {
        // Ottieni lo stato corrente dal backend
        const status = await api.getProjectStatus(projectId);
        
        // Se il progetto esiste nel backend ma non nel localStorage
        if (status && status.project_id) {
          const restoredProject: Project = {
            project_id: status.project_id,
            project_name: status.project_name || `Progetto ${status.project_id.substring(0, 8)}`,
            status: status.status,
            created_at: status.created_at || new Date().toISOString(),
            current_iteration: status.current_iteration
          };
          
          // Aggiungilo alla lista
          const success = addProject(restoredProject);
          if (success) {
            syncedCount++;
          }
        }
      } catch (error) {
        console.error(`Error syncing active project ${projectId}:`, error);
      }
    }
  }
  
  return syncedCount;
}, [getActiveProjects, getProject, addProject]);


  return {
    projects,
    metrics,
    isStorageAvailable,
    addProject,
    updateProject,
    removeProject,
    getProject,
    forceCleanup,
    clearAllProjects,
    exportProjects,
    importProjects,
    clearErrors,
    reload: loadProjects,
    trackActiveProject,
    untrackActiveProject,
    getActiveProjects,
    syncActiveProjects
  };
};