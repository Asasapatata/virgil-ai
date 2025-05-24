import React, { useState, useCallback } from 'react';
import type { NextPage } from 'next';
import Head from 'next/head';
import {
  Box,
  Container,
  Snackbar,
  Paper,
  IconButton,
  Tooltip,
  Badge
} from '@mui/material';
import {
  Code as CodeIcon,
  Add as AddIcon,
  Folder as FolderIcon,
  Warning as WarningIcon,
  CloudDownload as ExportIcon,
  CleaningServices as CleanupIcon,
  CloudUpload as CloudUploadIcon
} from '@mui/icons-material';

// Components
import Header from '../components/Header';
import ProjectSidebar from '../components/ProjectSidebar';
import OptimizedProjectList from '../components/OptimizedProjectList';
import ProjectDetails from '../components/ProjectDetails';
import CreateProjectDialog from '../components/CreateProjectDialog';
import ImportProjectDialog from '../components/ImportProjectDialog';
import ModifyProjectDialog from '../components/ModifyProjectDialog';
import { ErrorDisplay, NetworkError, SuccessMessage } from '../components/ErrorHandling';

// Hooks and API
import { useRobustStorage } from '../hooks/useRobustStorage';
import { Project } from '../hooks/useProjectStorage'; // Keep types
import CodeGeneratorAPI from '../src/services/api';

interface ErrorState {
  error: string | Error | null;
  context?: string;
  severity?: 'error' | 'warning' | 'info';
}

const HomePage: NextPage = () => {
  // Project management with robust storage
  const { 
    projects, 
    metrics,
    isStorageAvailable,
    addProject, 
    updateProject, 
    removeProject, 
    getProject,
    forceCleanup,
    exportProjects,
    clearErrors
  } = useRobustStorage();

  // State management
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorState, setErrorState] = useState<ErrorState>({ error: null });
  const [success, setSuccess] = useState<string>('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [modifyDialogOpen, setModifyDialogOpen] = useState(false); // Corretto: spostato all'interno del componente
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [polling, setPolling] = useState<Set<string>>(new Set());
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  // Add state for active projects tracking
  const [activeProjects, setActiveProjects] = useState<Set<string>>(new Set());
  
  const [api] = useState(new CodeGeneratorAPI());

  // Helper to track active projects
  const trackActiveProject = useCallback((projectId: string) => {
    setActiveProjects(prev => {
      const newSet = new Set(prev);
      newSet.add(projectId);
      return newSet;
    });
  }, []);

  // Helper to untrack active projects
  const untrackActiveProject = useCallback((projectId: string) => {
    setActiveProjects(prev => {
      const newSet = new Set(prev);
      newSet.delete(projectId);
      return newSet;
    });
  }, []);

  // Helper per gestire errori (ora include storage errors)
  const handleError = useCallback((error: string | Error, context?: string, severity: 'error' | 'warning' | 'info' = 'error') => {
    setErrorState({ error, context, severity });
  }, []);

  // Helper per dismissare errori
  const dismissError = useCallback(() => {
    setErrorState({ error: null });
    // Clear storage errors too
    if (metrics.errors.length > 0) {
      clearErrors();
    }
  }, [metrics.errors.length, clearErrors]);

  // Handler per stop generation
  const handleStopGeneration = async (projectId: string) => {
    try {
      // Chiamata API per fermare la generazione
      await api.stopGeneration(projectId);
      
      // Aggiorna lo stato del progetto usando updateProjectSafely
      updateProjectSafely(projectId, { 
        status: 'failed',
        stopped_by_user: true,
        stopped_at: new Date().toISOString()
      });
      
      // Rimuovi dai progetti in polling
      setPolling(prev => {
        const newSet = new Set(prev);
        newSet.delete(projectId);
        return newSet;
      });
      
      // Also untrack from active projects
      untrackActiveProject(projectId);
      
      // Mostra messaggio di successo
      setSuccess('Generazione fermata con successo');
      setSnackbarOpen(true);
    } catch (error: any) {
      console.error('Error stopping generation:', error);
      handleError(error.message || 'Errore durante l\'interruzione', 'Stop Generation', 'error');
    }
  };

  // Handler per gestire l'invio del form di modifica
  const handleModifyProject = async (modificationData: any) => {
    setLoading(true);
    
    try {
      // Aggiorna il progetto con lo stato di modifica
      updateProject(modificationData.project_id, { 
        status: 'processing',
        modification_id: modificationData.modification_id,
        current_iteration: 0,
        modification_mode: modificationData.mode
      });
      
      // Avvia polling per stato
      pollProjectStatus(modificationData.project_id);
      
      setSuccess('Modifica avviata con successo!');
      setSnackbarOpen(true);
    } catch (error: any) {
      console.error('Error starting modification:', error);
      handleError(error, 'Errore durante l\'avvio della modifica');
    } finally {
      setLoading(false);
    }
  };

  // Check for storage issues on mount
  React.useEffect(() => {
    if (!isStorageAvailable) {
      handleError(
        new Error('LocalStorage non disponibile. I progetti non verranno salvati.'),
        'Storage',
        'warning'
      );
    } else if (metrics.errors.length > 0) {
      // Show the most recent storage error
      const latestError = metrics.errors[metrics.errors.length - 1];
      handleError(
        new Error(latestError),
        'Storage',
        'warning'
      );
    }
  }, [isStorageAvailable, metrics.errors, handleError]);

  React.useEffect(() => {
  // Recupera i nomi personalizzati da localStorage
  try {
    const customNames = JSON.parse(localStorage.getItem('virgil_custom_project_names') || '{}');
    console.log('Loaded custom project names:', customNames);
    
    // Applica i nomi personalizzati ai progetti esistenti
    if (Object.keys(customNames).length > 0) {
      projects.forEach(project => {
        const customName = customNames[project.project_id];
        if (customName && project.project_name !== customName) {
          console.log(`Updating project ${project.project_id} name to "${customName}"`);
          updateProject(project.project_id, {
            ...project,
            project_name: customName
          });
        }
      });
    }
  } catch (error) {
    console.error('Error loading custom project names:', error);
  }
}, [projects.length]); // Esegui solo quando cambia il numero di progetti

// Hook personalizzato per gestire i nomi dei progetti (opzionale)
const useCustomProjectNames = () => {
  const [customNames, setCustomNames] = useState<Record<string, string>>({});
  
  // Carica i nomi da localStorage all'inizializzazione
  React.useEffect(() => {
    try {
      const savedNames = JSON.parse(localStorage.getItem('virgil_custom_project_names') || '{}');
      setCustomNames(savedNames);
    } catch (error) {
      console.error('Error loading custom project names:', error);
    }
  }, []);
  
  // Funzione per aggiungere o aggiornare un nome personalizzato
  const setCustomName = useCallback((projectId: string, name: string) => {
    setCustomNames(prev => {
      const newNames = { ...prev, [projectId]: name };
      localStorage.setItem('virgil_custom_project_names', JSON.stringify(newNames));
      return newNames;
    });
  }, []);
  
  // Funzione per ottenere un nome personalizzato
  const getCustomName = useCallback((projectId: string) => {
    return customNames[projectId] || null;
  }, [customNames]);
  
  return { customNames, setCustomName, getCustomName };
};

  // Helper per retry con context
  const handleRetryWithContext = useCallback((retryAction: () => Promise<void>) => {
    return async () => {
      dismissError();
      try {
        await retryAction();
      } catch (error: any) {
        handleError(error, 'Retry operation');
      }
    };
  }, [dismissError, handleError]);

  // Update selected project when projects change
  React.useEffect(() => {
    if (selectedProject) {
      const updatedProject = getProject(selectedProject.project_id);
      if (updatedProject) {
        setSelectedProject(updatedProject);
      } else {
        setSelectedProject(null);
      }
    }
  }, [projects, selectedProject, getProject]);

  // Helper per aggiornare progetti garantendo la persistenza di alcuni campi
const updateProjectSafely = useCallback((projectId: string, newData: any) => {
  const existingProject = getProject(projectId);
  
  if (existingProject) {
    // Crea un oggetto di aggiornamento che preserva alcuni campi critici
    const safeUpdate = {
      ...newData,
      // Mantiene sempre il nome del progetto originale
      project_name: existingProject.project_name
    };
    
    // Chiama la funzione di aggiornamento originale
    updateProject(projectId, safeUpdate);
  } else {
    // Se il progetto non esiste, aggiorna normalmente
    updateProject(projectId, newData);
  }
}, [getProject, updateProject]);


  // Polling for project status
  const pollProjectStatus = useCallback(async (projectId: string) => {
    if (polling.has(projectId)) return;

    // Aggiungi il progetto alla lista dei progetti attivi
    trackActiveProject(projectId);
    setPolling(prev => new Set(prev).add(projectId));
    
    const poll = async () => {
      try {
        const status = await api.getProjectStatus(projectId);
      
      // IMPORTANTE: Ottieni il progetto esistente prima dell'aggiornamento
      const existingProject = getProject(projectId);
      
      if (existingProject) {
        // Preserva il nome del progetto originale SOLO se lo status non fornisce un project_name personalizzato
        const updatedStatus = {
          ...status,
          // Se lo status contiene un project_name che NON è "Progetto ID", usalo
          // altrimenti mantieni il nome attuale
          project_name: (status.project_name && !status.project_name.includes(`Progetto ${projectId.substring(0, 8)}`))
            ? status.project_name
            : existingProject.project_name
        };
        
        updateProject(projectId, updatedStatus);
        console.log(`Aggiornato progetto ${projectId} con nome: ${updatedStatus.project_name}`);
      } else {
        console.log(`Progetto ${projectId} non trovato nella lista, lo aggiungo...`);
        // Crea un oggetto progetto minimo da aggiungere alla lista
        const newProject = {
          project_id: projectId,
          // Usa un nome più descrittivo o l'ID come fallback
          project_name: status.project_name || `Progetto ${projectId.substring(0, 8)}`,
          status: status.status,
          created_at: new Date().toISOString(),
          current_iteration: status.current_iteration
        };
        addProject(newProject);
        
        // Se non c'è un progetto selezionato, seleziona questo
        if (!selectedProject) {
          setSelectedProject(newProject);
        }
      
        }
        
        if (status.status === 'completed' || status.status === 'failed' || status.status === 'error') {
          setPolling(prev => {
            const newSet = new Set(prev);
            newSet.delete(projectId);
            return newSet;
          });
          
          // Rimuovi dalla lista dei progetti attivi quando completato
          untrackActiveProject(projectId);
          
          // Usa getProject per ottenere il nome aggiornato del progetto
          const currentProject = getProject(projectId);
          const projectName = currentProject?.project_name || `Progetto ${projectId.substring(0, 8)}`;
          
          if (status.status === 'completed') {
            setSuccess(`Progetto "${projectName}" completato!`);
            setSnackbarOpen(true);
          } else if (status.status === 'failed' || status.status === 'error') {
            handleError(
              new Error(`Progetto "${projectName}" fallito`),
              'Project Generation',
              'warning'
            );
          }
          return;
        }
        
        setTimeout(poll, 5000);
      } catch (error: any) {
        console.error('Error polling status:', error);
        setPolling(prev => {
          const newSet = new Set(prev);
          newSet.delete(projectId);
          return newSet;
        });
        
        // Rimuovi dalla lista dei progetti attivi
        untrackActiveProject(projectId);
        if (error.name === 'NetworkError' || error.message.includes('fetch')) {
          handleError(
            new Error('Problema di connessione durante il monitoraggio del progetto'),
            'Polling',
            'warning'
          );
        }
      }
    };
    
    poll();
  }, [polling, api, updateProject, getProject, addProject, handleError, selectedProject, trackActiveProject, untrackActiveProject, updateProjectSafely]);


  // Nuova funzione di polling modificata per preservare il nome personalizzato
const pollProjectStatusWithNamePreservation = useCallback(async (projectId: string, customName: string) => {
  if (polling.has(projectId)) return;

  // Aggiungi il progetto alla lista dei progetti attivi
  trackActiveProject(projectId);
  setPolling(prev => new Set(prev).add(projectId));
  
  // Carica nomi personalizzati da localStorage
  const customNames = JSON.parse(localStorage.getItem('virgil_custom_project_names') || '{}');
  
  const poll = async () => {
    try {
      const status = await api.getProjectStatus(projectId);
      
      // IMPORTANTE: Ottieni il progetto esistente prima dell'aggiornamento
      const existingProject = getProject(projectId);
      
      // Determina il nome da usare
      // 1. Usa quello personalizzato se esiste in localStorage
      // 2. Altrimenti usa quello esistente nel progetto
      // 3. Solo se nessuno dei precedenti è disponibile, usa quello dalla risposta dell'API
      const nameToUse = customNames[projectId] || 
                        (existingProject ? existingProject.project_name : null) || 
                        status.project_name;
      
      if (existingProject) {
        // Crea un oggetto di aggiornamento che preserva il nome
        const safeUpdate = {
          ...status,
          project_name: nameToUse
        };
        
        // Log di debug
        console.log(`Updating project ${projectId}`, {
          currentName: existingProject.project_name,
          apiName: status.project_name,
          preservedName: nameToUse,
          finalName: safeUpdate.project_name
        });
        
        updateProject(projectId, safeUpdate);
      } else {
        console.log(`Project ${projectId} not found in list, adding it...`);
        
        const newProject = {
          project_id: projectId,
          project_name: nameToUse,
          status: status.status,
          created_at: new Date().toISOString(),
          current_iteration: status.current_iteration
        };
        addProject(newProject);
        
        if (!selectedProject) {
          setSelectedProject(newProject);
        }
      }
      
      // Gestione dello stato completato/fallito/errore
      if (status.status === 'completed' || status.status === 'failed' || status.status === 'error') {
        setPolling(prev => {
          const newSet = new Set(prev);
          newSet.delete(projectId);
          return newSet;
        });
        
        untrackActiveProject(projectId);
        
        // Usa sempre il nome personalizzato anche qui
        if (status.status === 'completed') {
          setSuccess(`Progetto "${nameToUse}" completato!`);
          setSnackbarOpen(true);
        } else if (status.status === 'failed' || status.status === 'error') {
          handleError(
            new Error(`Progetto "${nameToUse}" fallito`),
            'Project Generation',
            'warning'
          );
        }
        return;
      }
      
      // Continua il polling
      setTimeout(poll, 5000);
    } catch (error: any) {
      console.error('Error polling status:', error);
      setPolling(prev => {
        const newSet = new Set(prev);
        newSet.delete(projectId);
        return newSet;
      });
      
      untrackActiveProject(projectId);
      
      if (error.name === 'NetworkError' || error.message.includes('fetch')) {
        handleError(
          new Error('Problema di connessione durante il monitoraggio del progetto'),
          'Polling',
          'warning'
        );
      }
    }
  };
  
  poll();
}, [polling, api, updateProject, getProject, addProject, handleError, selectedProject, trackActiveProject, untrackActiveProject]);


  ;

  const createProjectFromFile = async (
    file: File, 
    llmProvider: string = 'anthropic', 
    customProjectName: string = '',
    useSmartGeneration: boolean = true,
    overrides?: any
  ) => {
    setLoading(true);
    dismissError();
    
    try {
      console.log(`Creating project with custom name: "${customProjectName}"`);
      console.log('Smart generation enabled:', useSmartGeneration);
      console.log('Overrides:', overrides);
      
      let uploadResult;
      let projectId;
      
      // If we have a temp project ID from analysis, use it
      if (overrides?.tempProjectId) {
        projectId = overrides.tempProjectId;
        uploadResult = { project_id: projectId, project_name: customProjectName };
      } else {
        uploadResult = await (api.uploadRequirements as any)(file, customProjectName || null);
        projectId = uploadResult.project_id;
      }
      
      const finalProjectName = customProjectName.trim() 
        ? customProjectName.trim() 
        : uploadResult.project_name;
    
      const newProject: Project = {
        project_id: projectId,
        project_name: finalProjectName,
        status: 'uploaded',
        created_at: new Date().toISOString()
      };
      
      console.log('Adding new project to list:', newProject);
      addProject(newProject);

      // Save custom name in localStorage
      const customProjectNames = JSON.parse(localStorage.getItem('virgil_custom_project_names') || '{}');
      customProjectNames[projectId] = finalProjectName;
      localStorage.setItem('virgil_custom_project_names', JSON.stringify(customProjectNames));

      trackActiveProject(newProject.project_id);
      setSelectedProject(newProject);
      
      // Choose generation method
      if (useSmartGeneration) {
        console.log('Using smart generation with overrides:', overrides);
        
        await api.generateProjectSmart(
          projectId, 
          llmProvider, 
          overrides?.agentMode,
          overrides?.maxIterations
        );
        
        updateProjectSafely(projectId, { 
          status: 'processing',
          project_name: finalProjectName,
          generation_mode: 'smart',
          agent_mode: overrides?.agentMode,
          max_iterations: overrides?.maxIterations
        });
        
        setSuccess(`Progetto creato con generazione intelligente (${overrides?.agentMode})!`);
      } else {
        // Use standard multi-agent generation
        await api.generateProjectWithAgents(projectId, llmProvider, 10); 
        updateProjectSafely(projectId, { 
          status: 'processing',
          project_name: finalProjectName,
          generation_mode: 'standard'
        });
        
        setSuccess('Progetto creato con generazione standard!');
      }
      
      pollProjectStatusWithNamePreservation(projectId, finalProjectName);
      setSnackbarOpen(true);
        
    } catch (error: any) {
      console.error('Error creating project:', error);
      
      if (error.name === 'NetworkError') {
        handleError(
          new Error('Problema di connessione durante la creazione del progetto'),
          'Project Creation',
          'warning'
        );
      } else if (error.status === 413) {
        handleError(
          new Error('File troppo grande. Dimensione massima consentita: 10MB'),
          'File Upload',
          'error'
        );
      } else if (error.status === 400) {
        handleError(
          new Error('File non valido. Assicurati che sia un file YAML corretto'),
          'File Validation',
          'error'
        );
      } else {
        handleError(error, 'Project Creation');
      }
    } finally {
      setLoading(false);
    }
  };

  
  // Download project
  const handleDownloadProject = async (projectId: string, final = false) => {
    try {
      if (final) {
        await api.downloadFinalProject(projectId);
      } else {
        await api.downloadProject(projectId);
      }
      setSuccess(final ? 'Download progetto finale completato!' : 'Download progetto completato!');
      setSnackbarOpen(true);
    } catch (error: any) {
      console.error('Error downloading project:', error);
      handleError(
        error, 
        final ? 'Final Project Download' : 'Project Download',
        'error'
      );
    }
  };

  // Regenerate project
  const handleRegenerateProject = async (projectId: string) => {
    setLoading(true);
    dismissError();
    
    try {
      await api.generateProject(projectId, 'openai', 10);
      // Usa updateProjectSafely invece di updateProject direttamente
      updateProjectSafely(projectId, { 
        status: 'processing', 
        current_iteration: 0,
        test_results: undefined 
      });
      pollProjectStatus(projectId);
      setSuccess('Rigenerazione avviata!');
      setSnackbarOpen(true);
    } catch (error: any) {
      console.error('Error regenerating project:', error);
      handleError(error, 'Project Regeneration');
    } finally {
      setLoading(false);
    }
  };

  // Cleanup project iterations
  const handleCleanupProject = async (projectId: string) => {
    try {
      await api.cleanupProject(projectId, true);
      setSuccess('Pulizia iterazioni completata!');
      setSnackbarOpen(true);
    } catch (error: any) {
      console.error('Error cleaning up project:', error);
      handleError(error, 'Project Cleanup', 'warning');
    }
  };

  // Delete project from list
  const handleDeleteProject = (projectId: string) => {
    removeProject(projectId);
    if (selectedProject?.project_id === projectId) {
      setSelectedProject(null);
    }
    // Also untrack from active projects if needed
    untrackActiveProject(projectId);
    setSuccess('Progetto rimosso dalla lista');
    setSnackbarOpen(true);
  };

  // Storage maintenance actions
  const handleForceCleanup = useCallback(() => {
    const result = forceCleanup();
    setSuccess(`Pulizia completata: ${result.removed} progetti rimossi, ${result.remaining} conservati`);
    setSnackbarOpen(true);
  }, [forceCleanup]);

  const handleExportProjects = useCallback(() => {
    const success = exportProjects();
    if (success) {
      setSuccess('Export progetti completato!');
    } else {
      handleError(new Error('Errore durante l\'export'), 'Export', 'error');
    }
    setSnackbarOpen(true);
  }, [exportProjects, handleError]);

  // Handle settings click
  const handleSettingsClick = () => {
    // TODO: Implement settings dialog
    console.log('Settings clicked');
  };

  // Handle profile click  
  const handleProfileClick = () => {
    // TODO: Implement profile dialog
    console.log('Profile clicked');
  };

  // Gestione importazione progetti
  const handleImportProject = (projectData: any) => {
  const newProject: Project = {
    project_id: projectData.project_id,
    project_name: projectData.project_name,
    status: projectData.status || 'imported',
    created_at: projectData.created_at || new Date().toISOString(),
    imported: true,
    imported_files: projectData.imported_files,
    analysis: projectData.analysis
  };
  
  addProject(newProject);
  
  // Usa operatore ternario per gestire undefined
  const retrievedProject = getProject(projectData.project_id);
  setSelectedProject(retrievedProject ? retrievedProject : newProject);
  
  setSuccess('Progetto importato con successo!');
  setSnackbarOpen(true);
};

  return (
    <>
      <Head>
        <title>Virgil AI - Dashboard</title>
        <meta name="description" content="Generate and manage AI-powered code projects" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
        {/* Header with storage indicators */}
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Box sx={{ flex: 1 }}>
            <Header 
              onSettingsClick={handleSettingsClick}
              onProfileClick={handleProfileClick}
            />
          </Box>
          
          {/* Storage status indicators */}
          <Box sx={{ display: 'flex', gap: 1, mr: 2 }}>
            {!isStorageAvailable && (
              <Tooltip title="LocalStorage non disponibile">
                <IconButton color="warning" size="small">
                  <WarningIcon />
                </IconButton>
              </Tooltip>
            )}
            
            {metrics.errors.length > 0 && (
              <Tooltip title={`${metrics.errors.length} errori di storage`}>
                <IconButton color="warning" size="small" onClick={dismissError}>
                  <Badge badgeContent={metrics.errors.length} color="error">
                    <WarningIcon />
                  </Badge>
                </IconButton>
              </Tooltip>
            )}
            
            <Tooltip title="Esporta progetti">
              <IconButton size="small" onClick={handleExportProjects}>
                <ExportIcon />
              </IconButton>
            </Tooltip>
            
            {projects.length > 50 && (
              <Tooltip title="Pulizia storage">
                <IconButton size="small" onClick={handleForceCleanup}>
                  <CleanupIcon />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Box>

        {/* Error Display */}
        {errorState.error && (
          <Box sx={{ mx: 2, mt: 2 }}>
            <ErrorDisplay
              error={errorState.error}
              severity={errorState.severity}
              context={errorState.context}
              onDismiss={dismissError}
              onRetry={
                errorState.context === 'Project Creation' 
                  ? handleRetryWithContext(async () => {
                      console.log('Retry project creation');
                    })
                  : errorState.context === 'Project Regeneration' && selectedProject
                  ? handleRetryWithContext(async () => {
                      await handleRegenerateProject(selectedProject.project_id);
                    })
                  : errorState.context?.includes('Download') && selectedProject
                  ? handleRetryWithContext(async () => {
                      await handleDownloadProject(
                        selectedProject.project_id, 
                        errorState.context === 'Final Project Download'
                      );
                    })
                  : errorState.context === 'Storage'
                  ? () => dismissError()
                  : undefined
              }
              showDetails={errorState.severity === 'error'}
            />
          </Box>
        )}

        {/* Storage metrics info */}
        {metrics.storageSize > 7 * 1024 * 1024 && ( // Show when approaching 7MB
          <Box sx={{ mx: 2, mt: 1 }}>
            <ErrorDisplay
              error={`Storage quasi pieno: ${(metrics.storageSize / (1024 * 1024)).toFixed(1)}MB utilizzati`}
              severity="warning"
              context="Storage Space"
              onRetry={handleForceCleanup}
            />
          </Box>
        )}

        {/* Main Content */}
        <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          <Container maxWidth={false} sx={{ display: 'flex', height: '100%', py: 2, px: 2, gap: 2 }}>
            {/* Sidebar */}
            {projects.length > 20 ? (
              <OptimizedProjectList
                projects={projects}
                selectedProject={selectedProject}
                onSelectProject={setSelectedProject}
                onCreateProject={() => setCreateDialogOpen(true)}
                onImportProject={() => setImportDialogOpen(true)}
                loading={loading}
                polling={polling}
              />
            ) : (
              <ProjectSidebar
                projects={projects}
                selectedProject={selectedProject}
                onSelectProject={setSelectedProject}
                onCreateProject={() => setCreateDialogOpen(true)}
                onImportProject={() => setImportDialogOpen(true)}
                loading={loading}
                polling={polling}
              />
            )}

            {/* Main Content Area */}
            <Paper 
              elevation={1} 
              sx={{ 
                flex: 1, 
                borderRadius: 2,
                overflow: 'hidden',
                display: 'flex',
                flexDirection: 'column'
              }}
            >
              {!selectedProject ? (
                <Box 
                  sx={{ 
                    display: 'flex', 
                    flexDirection: 'column', 
                    alignItems: 'center', 
                    justifyContent: 'center', 
                    height: '100%',
                    textAlign: 'center',
                    p: 4
                  }}
                >
                  <CodeIcon sx={{ fontSize: 80, color: 'text.secondary', mb: 3 }} />
                  <Box sx={{ mb: 4 }}>
                    <h2 style={{ margin: 0, marginBottom: 16, fontSize: '2rem', fontWeight: 600 }}>
                      Benvenuto in Virgil AI
                    </h2>
                    <p style={{ margin: 0, color: '#666', fontSize: '1.1rem', maxWidth: 600 }}>
                      Seleziona un progetto dalla sidebar per visualizzare i dettagli e gestire la generazione del codice, 
                      oppure crea un nuovo progetto caricando un file YAML con i requisiti.
                    </p>
                  </Box>
                  
                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center', mb: 4 }}>
                    <button
                      onClick={() => setCreateDialogOpen(true)}
                      disabled={loading}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        padding: '12px 24px',
                        fontSize: '1rem',
                        fontWeight: 600,
                        backgroundColor: '#1976d2',
                        color: 'white',
                        border: 'none',
                        borderRadius: 8,
                        cursor: loading ? 'not-allowed' : 'pointer',
                        opacity: loading ? 0.6 : 1
                      }}
                    >
                      <AddIcon />
                      Crea Nuovo Progetto
                    </button>

                    <button
                      onClick={() => setImportDialogOpen(true)}
                      disabled={loading}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        padding: '12px 24px',
                        fontSize: '1rem',
                        fontWeight: 600,
                        backgroundColor: '#2e7d32', // Verde
                        color: 'white',
                        border: 'none',
                        borderRadius: 8,
                        cursor: loading ? 'not-allowed' : 'pointer',
                        opacity: loading ? 0.6 : 1
                      }}
                    >
                      <CloudUploadIcon />
                      Importa Progetto Esistente
                    </button>
                    
                    {projects.length > 0 && (
                      <button
                        onClick={() => setSelectedProject(projects[0])}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 8,
                          padding: '12px 24px',
                          fontSize: '1rem',
                          backgroundColor: 'transparent',
                          color: '#1976d2',
                          border: '1px solid #1976d2',
                          borderRadius: 8,
                          cursor: 'pointer'
                        }}
                      >
                        <FolderIcon />
                        Vai all'ultimo progetto
                      </button>
                    )}
                  </Box>
                  
                  {/* Quick Stats with storage info */}
                  {projects.length > 0 && (
                    <Box sx={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                      <Box sx={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#1976d2' }}>
                          {metrics.projectCount}
                        </div>
                        <div style={{ fontSize: '0.875rem', color: '#666' }}>
                          Progetti totali
                        </div>
                      </Box>
                      <Box sx={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#2e7d32' }}>
                          {projects.filter(p => p.status === 'completed').length}
                        </div>
                        <div style={{ fontSize: '0.875rem', color: '#666' }}>
                          Completati
                        </div>
                      </Box>
                      <Box sx={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#ed6c02' }}>
                          {polling.size}
                        </div>
                        <div style={{ fontSize: '0.875rem', color: '#666' }}>
                          In elaborazione
                        </div>
                      </Box>
                      <Box sx={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#666' }}>
                          {(metrics.storageSize / (1024 * 1024)).toFixed(1)}MB
                        </div>
                        <div style={{ fontSize: '0.875rem', color: '#666' }}>
                          Storage utilizzato
                        </div>
                      </Box>
                    </Box>
                  )}
                </Box>
              ) : (
                <ProjectDetails
                  project={selectedProject}
                  onDownload={handleDownloadProject}
                  onRegenerate={handleRegenerateProject}
                  onCleanup={handleCleanupProject}
                  onDelete={handleDeleteProject}
                  onStopGeneration={handleStopGeneration}
                  onModify={() => setModifyDialogOpen(true)} 
                  loading={loading}
                  isPolling={polling.has(selectedProject.project_id)}
                />
              )}
            </Paper>
          </Container>
        </Box>

        {/* Dialogs */}
        <CreateProjectDialog 
          open={createDialogOpen}
          onClose={() => setCreateDialogOpen(false)}
          onSuccess={createProjectFromFile}
          loading={loading}
        />

        {/* Aggiunto correttamente il ModifyProjectDialog */}
        {modifyDialogOpen && selectedProject && (
          <ModifyProjectDialog
            open={modifyDialogOpen}
            onClose={() => setModifyDialogOpen(false)}
            onSuccess={handleModifyProject}
            project={{
              project_id: selectedProject.project_id,
              project_name: selectedProject.project_name
            }}
            loading={loading}
            api={api}
          />
        )}

        {/* ImportProjectDialog */}
        <ImportProjectDialog
          open={importDialogOpen}
          onClose={() => setImportDialogOpen(false)}
          onSuccess={handleImportProject}
          loading={loading}
          api={api}
        />

        {/* Success Message */}
        {success && (
          <Box sx={{ position: 'fixed', top: 100, right: 16, zIndex: 1300 }}>
            <SuccessMessage
              message={success}
              onDismiss={() => {
                setSuccess('');
                setSnackbarOpen(false);
              }}
            />
          </Box>
        )}
      </Box>
    </>
  );
};

export default HomePage;