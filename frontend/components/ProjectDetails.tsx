// ProjectDetails.tsx - File completamente unificato
import React, { useState } from 'react';
import {
  Box,
  Typography,
  Chip,
  Button,
  IconButton,
  Menu,
  MenuItem,
  Divider,
  CircularProgress,
  LinearProgress,
  Tabs,
  Tab,
  Grid,
  Card,
  CardContent,
  Alert,
  ListItemIcon,
  Paper
} from '@mui/material';
import {
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  MoreVert as MoreVertIcon,
  CleaningServices as CleaningServicesIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Folder as FolderIcon,
  Stop as StopIcon,
  Edit as EditIcon,
  Code as CodeIcon,
  Storage as StorageIcon
} from '@mui/icons-material';
import { Project } from '../hooks/useProjectStorage';
import StopGenerationButton from './StopGenerationButton';
import CodeGeneratorAPI from '../src/services/api';

interface ProjectDetailsProps {
  project: Project;
  onDownload: (projectId: string, final?: boolean) => void;
  onRegenerate: (projectId: string) => void;
  onCleanup: (projectId: string) => void;
  onDelete: (projectId: string) => void;
  onStopGeneration?: (projectId: string) => void;
  onModify?: () => void;
  loading: boolean;
  isPolling: boolean;
}

const ProjectDetails: React.FC<ProjectDetailsProps> = ({
  project,
  onDownload,
  onRegenerate,
  onCleanup,
  onDelete,
  onStopGeneration,
  onModify,
  loading,
  isPolling
}) => {
  const [tabValue, setTabValue] = useState(0);
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  const api = new CodeGeneratorAPI();

  const getStatusColor = (status: Project['status']) => {
    switch (status) {
      case 'completed': return 'success';
      case 'processing':
      case 'generating_code':
      case 'generating_tests':
      case 'running_tests': return 'warning';
      case 'failed':
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: Project['status']) => {
    switch (status) {
      case 'completed': return <CheckCircleIcon />;
      case 'processing':
      case 'generating_code':
      case 'generating_tests':
      case 'running_tests': return <ScheduleIcon />;
      case 'failed':
      case 'error': return <ErrorIcon />;
      default: return <FolderIcon />;
    }
  };

  const getStatusLabel = (status: Project['status']) => {
    switch (status) {
      case 'uploaded': return 'Caricato';
      case 'imported': return 'Importato';
      case 'processing': return 'In elaborazione';
      case 'generating_code': return 'Generando codice';
      case 'generating_tests': return 'Generando test';
      case 'running_tests': return 'Eseguendo test';
      case 'completed': return 'Completato';
      case 'failed': return 'Fallito';
      case 'error': return 'Errore';
      default: return status;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const isGenerating = () => {
    return ['processing', 'generating_code', 'generating_tests', 'running_tests'].includes(project.status);
  };

  const canModify = () => {
    return !isGenerating() && project.status !== 'uploaded';
  };

  const handleStopSuccess = () => {
    if (onStopGeneration) {
      onStopGeneration(project.project_id);
    }
  };

  const handleStopError = (error: Error) => {
    console.error('Stop generation error:', error);
    // Qui potresti aggiungere una gestione più sofisticata degli errori
  };

  // Add a new tab for import details if this is an imported project
  const tabs = [
    { label: 'Panoramica', id: 'overview' },
    { label: 'Test Results', id: 'tests', disabled: !project.test_results },
    { label: 'Log', id: 'logs' }
  ];

  // Add import tab if applicable
  if (project.imported && project.imported_files) {
    tabs.splice(1, 0, { label: 'Import Details', id: 'import', disabled: false });
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Project Header */}
      <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
              {project.project_name}
            </Typography>
            {project.description && (
              <Typography variant="body1" color="text.secondary" gutterBottom>
                {project.description}
              </Typography>
            )}
            <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
              <Chip 
                label={getStatusLabel(project.status)} 
                color={getStatusColor(project.status)}
                icon={getStatusIcon(project.status)}
              />
              {project.current_iteration !== undefined && (
                <Chip 
                  label={`Iterazione ${project.current_iteration}/10`}
                  variant="outlined"
                />
              )}
              {project.has_final && (
                <Chip 
                  label="Versione finale disponibile"
                  color="success"
                  variant="outlined"
                />
              )}
              {project.imported && (
                <Chip 
                  label="Progetto importato"
                  color="primary"
                  variant="outlined"
                  icon={<CodeIcon />}
                />
              )}
              {project.modification_mode && (
                <Chip 
                  label={`Modificato (${project.modification_mode === 'incremental' ? 'Incrementale' : 'Riscrittura'})` }
                  color="info"
                  variant="outlined"
                  icon={<EditIcon />}
                />
              )}
              {isPolling && (
                <Chip 
                  label="Monitoraggio attivo"
                  color="warning"
                  variant="outlined"
                  icon={<CircularProgress size={16} />}
                />
              )}
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {/* Modification Button */}
            {canModify() && onModify && (
              <Button
                variant="outlined"
                color="primary"
                startIcon={<EditIcon />}
                onClick={onModify}
                disabled={loading}
              >
                Modifica Progetto
              </Button>
            )}

            {/* Stop Generation Button - only show if generating */}
            {isGenerating() && onStopGeneration && (
              <StopGenerationButton
                projectId={project.project_id}
                projectName={project.project_name}
                onStopSuccess={handleStopSuccess}
                onError={handleStopError}
                api={api}
                disabled={loading}
              />
            )}

            {project.status === 'completed' && (
              <>
                <Button
                  variant="contained"
                  startIcon={<DownloadIcon />}
                  onClick={() => onDownload(project.project_id)}
                >
                  Download Ultima Iterazione
                </Button>
                {project.has_final && (
                  <Button
                    variant="contained"
                    color="success"
                    startIcon={<DownloadIcon />}
                    onClick={() => onDownload(project.project_id, true)}
                  >
                    Download Finale
                  </Button>
                )}
              </>
            )}
            
            {(project.status === 'failed' || project.status === 'error') && (
              <Button
                variant="contained"
                color="primary"
                startIcon={<RefreshIcon />}
                onClick={() => onRegenerate(project.project_id)}
                disabled={loading}
              >
                Riprova Generazione
              </Button>
            )}

            <IconButton
              onClick={(e) => setMenuAnchorEl(e.currentTarget)}
            >
              <MoreVertIcon />
            </IconButton>
          </Box>
        </Box>

        {/* Progress bar for active generation */}
        {project.current_iteration !== undefined && 
         project.status !== 'completed' && 
         project.status !== 'failed' && (
          <Box sx={{ mt: 2 }}>
            <LinearProgress 
              variant="determinate" 
              value={(project.current_iteration / 10) * 100}
              sx={{ height: 8, borderRadius: 1 }}
            />
            <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
              Progresso: {project.current_iteration}/10 iterazioni
            </Typography>
          </Box>
        )}
      </Box>

      {/* Project Content */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        <Box sx={{ p: 3 }}>
          <Tabs 
            value={tabValue} 
            onChange={(_, newValue) => setTabValue(newValue)}
            sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}
          >
            {tabs.map((tab, index) => (
              <Tab 
                key={tab.id} 
                label={tab.label} 
                disabled={tab.disabled}
                value={index}
              />
            ))}
          </Tabs>

          {/* Overview Tab */}
          {tabValue === 0 && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Informazioni Progetto
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">ID:</Typography>
                        <Typography variant="body2" fontFamily="monospace">
                          #{project.project_id}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Creato:</Typography>
                        <Typography variant="body2">
                          {formatDate(project.created_at)}
                        </Typography>
                      </Box>
                      {project.updated_at && (
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="text.secondary">Aggiornato:</Typography>
                          <Typography variant="body2">
                            {formatDate(project.updated_at)}
                          </Typography>
                        </Box>
                      )}
                      {project.imported && (
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="text.secondary">Tipo:</Typography>
                          <Typography variant="body2">
                            Progetto importato
                          </Typography>
                        </Box>
                      )}
                      <Divider />
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Stato:</Typography>
                        <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                          {getStatusLabel(project.status)}
                        </Typography>
                      </Box>
                      {project.current_iteration !== undefined && (
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="text.secondary">Iterazione:</Typography>
                          <Typography variant="body2">
                            {project.current_iteration}/10
                          </Typography>
                        </Box>
                      )}
                      {project.stopped_by_user && (
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="text.secondary">Nota:</Typography>
                          <Typography variant="body2" color="warning.main">
                            Fermato manualmente
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Azioni Rapide
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                      {isGenerating() && onStopGeneration && (
                        <Button
                          fullWidth
                          variant="outlined"
                          color="warning"
                          startIcon={<StopIcon />}
                          onClick={() => {
                            // Usa il pulsante StopGenerationButton per il dialogo di conferma
                            // qui possiamo solo simulare un click 
                            const stopButton = document.querySelector('button[data-stop-generation="true"]');
                            if (stopButton instanceof HTMLElement) {
                              stopButton.click();
                            } else {
                              // Fallback
                              if (onStopGeneration && window.confirm("Sei sicuro di voler fermare la generazione?")) {
                                onStopGeneration(project.project_id);
                              }
                            }
                          }}
                        >
                          Ferma Generazione
                        </Button>
                      )}

                      {canModify() && onModify && (
                        <Button
                          fullWidth
                          variant="outlined"
                          color="primary"
                          startIcon={<EditIcon />}
                          onClick={onModify}
                          disabled={loading}
                        >
                          Modifica Progetto
                        </Button>
                      )}

                      {project.status === 'completed' && (
                        <>
                          <Button
                            fullWidth
                            variant="outlined"
                            startIcon={<DownloadIcon />}
                            onClick={() => onDownload(project.project_id)}
                          >
                            Download Ultima Iterazione
                          </Button>
                          {project.has_final && (
                            <Button
                              fullWidth
                              variant="outlined"
                              color="success"
                              startIcon={<DownloadIcon />}
                              onClick={() => onDownload(project.project_id, true)}
                            >
                              Download Progetto Finale
                            </Button>
                          )}
                          <Button
                            fullWidth
                            variant="outlined"
                            startIcon={<RefreshIcon />}
                            onClick={() => onRegenerate(project.project_id)}
                            disabled={loading}
                          >
                            Rigenera Progetto
                          </Button>
                          <Button
                            fullWidth
                            variant="outlined"
                            color="warning"
                            startIcon={<CleaningServicesIcon />}
                            onClick={() => onCleanup(project.project_id)}
                          >
                            Pulisci Iterazioni
                          </Button>
                        </>
                      )}
                      
                      {(project.status === 'failed' || project.status === 'error') && (
                        <Button
                          fullWidth
                          variant="contained"
                          color="primary"
                          startIcon={<RefreshIcon />}
                          onClick={() => onRegenerate(project.project_id)}
                          disabled={loading}
                        >
                          Riprova Generazione
                        </Button>
                      )}

                      {(project.status === 'processing' || 
                        project.status === 'generating_code' || 
                        project.status === 'generating_tests' || 
                        project.status === 'running_tests') && (
                        <Alert severity="info" sx={{ mt: 1 }}>
                          <Typography variant="body2">
                            Generazione in corso... Il progresso viene aggiornato automaticamente.
                          </Typography>
                        </Alert>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          {/* Import Details Tab - only show if this is an imported project */}
          {project.imported && project.imported_files && tabValue === 1 && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Dettagli Importazione
                </Typography>

                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle1" gutterBottom>
                          Files Importati
                        </Typography>
                        <Typography variant="h4" color="primary.main" gutterBottom>
                          {project.imported_files.length}
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 2 }}>
                          {project.imported_files.slice(0, 10).map((file, index) => (
                            <Chip
                              key={index}
                              label={file}
                              size="small"
                              variant="outlined"
                            />
                          ))}
                          {project.imported_files.length > 10 && (
                            <Chip
                              label={`+${project.imported_files.length - 10} altri`}
                              size="small"
                              color="primary"
                            />
                          )}
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>

                  {project.analysis && (
                    <Grid item xs={12} md={6}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="subtitle1" gutterBottom>
                            Analisi del Progetto
                          </Typography>
                          
                          {project.analysis.technologies && (
                            <Box sx={{ mb: 2 }}>
                              <Typography variant="body2" color="text.secondary" gutterBottom>
                                Tecnologie rilevate
                              </Typography>
                              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                {project.analysis.technologies.map((tech, index) => (
                                  <Chip
                                    key={index}
                                    label={tech}
                                    size="small"
                                    variant="outlined"
                                  />
                                ))}
                              </Box>
                            </Box>
                          )}
                          
                          {project.analysis.estimated_complexity && (
                            <Box sx={{ mb: 2 }}>
                              <Typography variant="body2" color="text.secondary" gutterBottom>
                                Complessità stimata
                              </Typography>
                              <Chip
                                label={project.analysis.estimated_complexity.toUpperCase()}
                                color={
                                  project.analysis.estimated_complexity === 'high' ? 'error' :
                                  project.analysis.estimated_complexity === 'medium' ? 'warning' : 'success'
                                }
                                variant="outlined"
                              />
                            </Box>
                          )}
                          
                          {project.analysis.suggestions && project.analysis.suggestions.length > 0 && (
                            <Box>
                              <Typography variant="body2" color="text.secondary" gutterBottom>
                                Suggerimenti
                              </Typography>
                              <Paper variant="outlined" sx={{ p: 1.5 }}>
                                <Box component="ul" sx={{ m: 0, pl: 2 }}>
                                  {project.analysis.suggestions.map((suggestion, index) => (
                                    <li key={index}>
                                      <Typography variant="body2">{suggestion}</Typography>
                                    </li>
                                  ))}
                                </Box>
                              </Paper>
                            </Box>
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                  )}
                </Grid>
              </CardContent>
            </Card>
          )}

          {/* Test Results Tab - adjusted index for imported projects */}
          {tabValue === (project.imported ? 2 : 1) && project.test_results && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Risultati Test
                </Typography>
                <Grid container spacing={2}>
                  {project.test_results.frontend && (
                    <Grid item xs={12} md={4}>
                      <Card variant="outlined">
                        <CardContent sx={{ textAlign: 'center' }}>
                          <Box sx={{ 
                            color: project.test_results.frontend.success ? 'success.main' : 'error.main',
                            mb: 1
                          }}>
                            {project.test_results.frontend.success ? 
                              <CheckCircleIcon fontSize="large" /> : 
                              <ErrorIcon fontSize="large" />
                            }
                          </Box>
                          <Typography variant="h6">Frontend</Typography>
                          <Chip 
                            label={project.test_results.frontend.success ? 'Successo' : 'Fallito'}
                            color={project.test_results.frontend.success ? 'success' : 'error'}
                            size="small"
                            sx={{ mt: 1 }}
                          />
                        </CardContent>
                      </Card>
                    </Grid>
                  )}
                  
                  {project.test_results.backend && (
                    <Grid item xs={12} md={4}>
                      <Card variant="outlined">
                        <CardContent sx={{ textAlign: 'center' }}>
                          <Box sx={{ 
                            color: project.test_results.backend.success ? 'success.main' : 'error.main',
                            mb: 1
                          }}>
                            {project.test_results.backend.success ? 
                              <CheckCircleIcon fontSize="large" /> : 
                              <ErrorIcon fontSize="large" />
                            }
                          </Box>
                          <Typography variant="h6">Backend</Typography>
                          <Chip 
                            label={project.test_results.backend.success ? 'Successo' : 'Fallito'}
                            color={project.test_results.backend.success ? 'success' : 'error'}
                            size="small"
                            sx={{ mt: 1 }}
                          />
                        </CardContent>
                      </Card>
                    </Grid>
                  )}
                  
                  {project.test_results.e2e && (
                    <Grid item xs={12} md={4}>
                      <Card variant="outlined">
                        <CardContent sx={{ textAlign: 'center' }}>
                          <Box sx={{ 
                            color: project.test_results.e2e.success ? 'success.main' : 'error.main',
                            mb: 1
                          }}>
                            {project.test_results.e2e.success ? 
                              <CheckCircleIcon fontSize="large" /> : 
                              <ErrorIcon fontSize="large" />
                            }
                          </Box>
                          <Typography variant="h6">E2E</Typography>
                          <Chip 
                            label={project.test_results.e2e.success ? 'Successo' : 'Fallito'}
                            color={project.test_results.e2e.success ? 'success' : 'error'}
                            size="small"
                            sx={{ mt: 1 }}
                          />
                        </CardContent>
                      </Card>
                    </Grid>
                  )}
                </Grid>
                
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                  <strong>Test complessivo:</strong> {' '}
                  {project.test_results.success ? 'Tutti i test sono passati' : 'Alcuni test sono falliti'}
                </Typography>
              </CardContent>
            </Card>
          )}

          {/* Logs Tab - adjusted index for imported projects */}
          {tabValue === (project.imported ? 3 : 2) && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Log di Generazione
                </Typography>
                <Box 
                  sx={{ 
                    bgcolor: 'grey.900', 
                    p: 2, 
                    borderRadius: 1,
                    fontFamily: 'monospace',
                    fontSize: '0.875rem',
                    color: 'common.white',
                    maxHeight: 400,
                    overflow: 'auto'
                  }}
                >
                  <Typography component="div" sx={{ whiteSpace: 'pre-wrap' }}>
                    {`[${formatDate(project.created_at)}] Progetto creato: ${project.project_name}
[${formatDate(project.created_at)}] Status: ${project.status === 'imported' ? 'importato' : 'caricato'}
${project.imported ? `[${formatDate(project.created_at)}] Importati ${project.imported_files?.length || '?'} file` : ''}
${project.current_iteration ? `[${formatDate(project.updated_at || project.created_at)}] Iterazione ${project.current_iteration} completata` : ''}
${project.status === 'processing' ? `[${formatDate(project.updated_at || project.created_at)}] Generazione in corso...` : ''}
${project.status === 'generating_code' ? `[${formatDate(project.updated_at || project.created_at)}] Generazione codice in corso...` : ''}
${project.status === 'generating_tests' ? `[${formatDate(project.updated_at || project.created_at)}] Generazione test in corso...` : ''}
${project.status === 'running_tests' ? `[${formatDate(project.updated_at || project.created_at)}] Esecuzione test in corso...` : ''}
${project.stopped_by_user ? `[${formatDate(project.stopped_at || project.updated_at || project.created_at)}] Generazione fermata manualmente` : ''}
${project.status === 'completed' ? `[${formatDate(project.updated_at || project.created_at)}] Generazione completata con successo` : ''}
${project.status === 'failed' && !project.stopped_by_user ? `[${formatDate(project.updated_at || project.created_at)}] Generazione fallita` : ''}
${project.test_results ? `[${formatDate(project.updated_at || project.created_at)}] Test completati: ${project.test_results.success ? 'SUCCESSO' : 'FALLITO'}` : ''}
${isPolling ? '[IN TEMPO REALE] Monitoraggio attivo...' : ''}`}
                  </Typography>
                </Box>
                {isPolling && (
                  <Box sx={{ mt: 2, display: 'flex', alignItems: 'center' }}>
                    <CircularProgress size={16} sx={{ mr: 1 }} />
                    <Typography variant="caption" color="primary">
                      Aggiornamento automatico attivo
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          )}
        </Box>
      </Box>

      {/* Context Menu - Updated with newer options */}
      <Menu
        anchorEl={menuAnchorEl}
        open={Boolean(menuAnchorEl)}
        onClose={() => setMenuAnchorEl(null)}
      >
        {/* Modify option */}
        {canModify() && onModify && (
          <MenuItem 
            onClick={() => {
              setMenuAnchorEl(null);
              onModify();
            }}
            disabled={loading}
          >
            <ListItemIcon>
              <EditIcon />
            </ListItemIcon>
            Modifica Progetto
          </MenuItem>
        )}

        {/* Stop Generation option */}
        {isGenerating() && onStopGeneration && (
          <MenuItem 
            onClick={() => {
              setMenuAnchorEl(null);
              // Usa il pulsante StopGenerationButton per il dialogo di conferma
              const stopButton = document.querySelector('button[data-stop-generation="true"]');
              if (stopButton instanceof HTMLElement) {
                stopButton.click();
              } else {
                // Fallback
                if (onStopGeneration && window.confirm("Sei sicuro di voler fermare la generazione?")) {
                  onStopGeneration(project.project_id);
                }
              }
            }}
            disabled={loading}
          >
            <ListItemIcon>
              <StopIcon color="warning" />
            </ListItemIcon>
            Ferma Generazione
          </MenuItem>
        )}

        <MenuItem 
          onClick={() => {
            setMenuAnchorEl(null);
            onRegenerate(project.project_id);
          }}
          disabled={loading || isGenerating()}
        >
          <ListItemIcon>
            <RefreshIcon />
          </ListItemIcon>
          Rigenera Progetto
        </MenuItem>
        <MenuItem 
          onClick={() => {
            setMenuAnchorEl(null);
            onCleanup(project.project_id);
          }}
        >
          <ListItemIcon>
            <CleaningServicesIcon />
          </ListItemIcon>
          Pulisci Iterazioni
        </MenuItem>
        <Divider />
        <MenuItem 
          onClick={() => {
            setMenuAnchorEl(null);
            onDelete(project.project_id);
          }}
          sx={{ color: 'error.main' }}
        >
          <ListItemIcon>
            <DeleteIcon sx={{ color: 'error.main' }} />
          </ListItemIcon>
          Rimuovi dalla Lista
        </MenuItem>
      </Menu>
      
      {/* Hidden Stop Button to provide access to the StopGenerationButton dialog */}
      {isGenerating() && onStopGeneration && (
        <StopGenerationButton
          projectId={project.project_id}
          projectName={project.project_name}
          onStopSuccess={handleStopSuccess}
          onError={handleStopError}
          api={api}
          disabled={loading}
          sx={{ display: 'none' }} // Nascosto visivamente
          data-stop-generation="true" // Attributo per identificarlo
        />
      )}
    </Box>
  );
};

export default ProjectDetails;