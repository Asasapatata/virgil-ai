// components/CreateProjectDialog.tsx
import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  TextField,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Alert,
  AlertTitle,
  Divider,
  Paper,
  Grid,
  Fade,
  LinearProgress
} from '@mui/material';
import {
  Add as AddIcon,
  CloudUpload as CloudUploadIcon,
  CheckCircle as CheckCircleIcon,
  Autorenew as AutorenewIcon,
  ExpandMore as ExpandMoreIcon,
  Psychology as PsychologyIcon,
  Speed as SpeedIcon,
  Engineering as EngineeringIcon,
  Groups as GroupsIcon,
  Timer as TimerIcon,
  Folder as FolderIcon,
  Analytics as AnalyticsIcon
} from '@mui/icons-material';

interface CreateProjectDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: (file: File, llmProvider: string, projectName: string, useSmartGeneration?: boolean, overrides?: any) => void;
  loading: boolean;
  api?: any; // Your CodeGeneratorAPI instance
}

const CreateProjectDialog: React.FC<CreateProjectDialogProps> = ({
  open,
  onClose,
  onSuccess,
  loading,
  api
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [llmProvider, setLlmProvider] = useState('anthropic');
  const [dragOver, setDragOver] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [projectNameError, setProjectNameError] = useState('');
  
  // Smart generation states
  const [useSmartGeneration, setUseSmartGeneration] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [selectedAgentMode, setSelectedAgentMode] = useState('');
  const [selectedMaxIterations, setSelectedMaxIterations] = useState(0);
  const [agentModes, setAgentModes] = useState<any>(null);
  const [tempProjectId, setTempProjectId] = useState<string | null>(null);

  // Load agent modes info when dialog opens
  useEffect(() => {
    if (open && api && !agentModes) {
      loadAgentModes();
    }
  }, [open, api]);

  const loadAgentModes = async () => {
    try {
      const modes = await api.getAgentModes();
      setAgentModes(modes);
    } catch (error) {
      console.error('Error loading agent modes:', error);
    }
  };

  // Analyze file when uploaded
  useEffect(() => {
    if (file && useSmartGeneration && api && !analyzing) {
      analyzeFile();
    }
  }, [file, useSmartGeneration, api]);

  const analyzeFile = async () => {
    if (!file || !api) return;
    
    setAnalyzing(true);
    try {
      // First upload the file to get a project ID
      const uploadResult = await api.uploadRequirements(file, projectName || null);
      setTempProjectId(uploadResult.project_id);
      
      // Then analyze the requirements
      const analysisResult = await api.analyzeRequirements(uploadResult.project_id);
      setAnalysis(analysisResult.analysis);
      
      // Set recommended values
      setSelectedAgentMode(analysisResult.analysis.agent_mode);
      setSelectedMaxIterations(analysisResult.analysis.max_iterations);
      
    } catch (error) {
      console.error('Error analyzing file:', error);
      // Fallback to non-smart generation if analysis fails
      setUseSmartGeneration(false);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSubmit = () => {
    if (!file) return;
    
    // Validazione del nome del progetto
    if (!projectName.trim()) {
      setProjectNameError('Il nome del progetto è obbligatorio');
      return;
    }
    
    // Prepare overrides for smart generation
    const overrides = useSmartGeneration ? {
      agentMode: selectedAgentMode,
      maxIterations: selectedMaxIterations,
      tempProjectId: tempProjectId // Pass the temp project ID to avoid re-upload
    } : undefined;
    
    onSuccess(file, llmProvider, projectName, useSmartGeneration, overrides);
    handleClose();
  };

  const handleClose = () => {
    onClose();
    setFile(null);
    setDragOver(false);
    setProjectName('');
    setProjectNameError('');
    setAnalysis(null);
    setAnalyzing(false);
    setTempProjectId(null);
    setShowAdvanced(false);
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile && (selectedFile.name.endsWith('.yaml') || selectedFile.name.endsWith('.yml'))) {
      setFile(selectedFile);
      
      // Imposta automaticamente il nome del progetto dal nome del file (senza estensione)
      if (!projectName) {
        const defaultName = selectedFile.name.replace(/\.(yaml|yml)$/, '');
        setProjectName(defaultName);
      }
    }
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    setDragOver(false);
    const droppedFile = event.dataTransfer.files[0];
    if (droppedFile && (droppedFile.name.endsWith('.yaml') || droppedFile.name.endsWith('.yml'))) {
      setFile(droppedFile);
      
      // Imposta automaticamente il nome del progetto dal nome del file (senza estensione)
      if (!projectName) {
        const defaultName = droppedFile.name.replace(/\.(yaml|yml)$/, '');
        setProjectName(defaultName);
      }
    }
  };

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleProjectNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setProjectName(e.target.value);
    setProjectNameError('');
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'simple': return 'success';
      case 'moderate': return 'info';
      case 'complex': return 'warning';
      case 'enterprise': return 'error';
      default: return 'info';
    }
  };

  const getAgentIcon = (mode: string) => {
    switch (mode) {
      case 'original': return <SpeedIcon />;
      case 'enhanced_generator': return <EngineeringIcon />;
      case 'updated_orchestrator': return <AnalyticsIcon />;
      case 'multi_agent': return <GroupsIcon />;
      default: return <PsychologyIcon />;
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <AddIcon sx={{ mr: 1 }} />
          Nuovo Progetto
        </Box>
      </DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 1 }}>
          {/* File Upload Section */}
          <Typography variant="h6" gutterBottom>
            1. Carica File Requisiti
          </Typography>
          <Box
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            sx={{
              border: 2,
              borderColor: dragOver ? 'primary.main' : file ? 'success.main' : 'grey.300',
              borderStyle: 'dashed',
              borderRadius: 2,
              p: 3,
              textAlign: 'center',
              bgcolor: dragOver ? 'primary.lighter' : file ? 'success.lighter' : 'grey.50',
              cursor: 'pointer',
              transition: 'all 0.2s',
              mb: 3
            }}
            onClick={() => document.getElementById('file-input')?.click()}
          >
            <input
              id="file-input"
              type="file"
              accept=".yaml,.yml"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
            {file ? (
              <Box>
                <CheckCircleIcon sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
                <Typography variant="body1" gutterBottom>
                  File caricato: <strong>{file.name}</strong>
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {(file.size / 1024).toFixed(1)} KB
                </Typography>
              </Box>
            ) : (
              <Box>
                <CloudUploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                <Typography variant="body1" gutterBottom>
                  Trascina qui il file YAML o clicca per selezionare
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Formati supportati: .yaml, .yml
                </Typography>
              </Box>
            )}
          </Box>

          {/* Project Name */}
          <Typography variant="h6" gutterBottom>
            2. Nome del Progetto
          </Typography>
          <TextField
            fullWidth
            label="Nome del Progetto"
            variant="outlined"
            value={projectName}
            onChange={handleProjectNameChange}
            error={!!projectNameError}
            helperText={projectNameError || "Inserisci un nome per il tuo progetto"}
            sx={{ mb: 3 }}
            required
          />

          {/* LLM Provider Selection */}
          <Typography variant="h6" gutterBottom>
            3. Seleziona AI Model
          </Typography>
          <FormControl fullWidth sx={{ mb: 3 }}>
            <InputLabel>AI Model</InputLabel>
            <Select
              value={llmProvider}
              label="AI Model"
              onChange={(e) => setLlmProvider(e.target.value)}
            >
              <MenuItem value="anthropic">Claude (Anthropic) - Consigliato</MenuItem>
              <MenuItem value="openai">ChatGPT (OpenAI)</MenuItem>
              <MenuItem value="deepseek">DeepSeek (RunPod)</MenuItem>
            </Select>
          </FormControl>

          {/* Smart Generation Toggle */}
          <Typography variant="h6" gutterBottom>
            4. Modalità di Generazione
          </Typography>
          <Box sx={{ mb: 3 }}>
            <FormControl fullWidth>
              <InputLabel>Modalità Generazione</InputLabel>
              <Select
                value={useSmartGeneration ? 'smart' : 'standard'}
                label="Modalità Generazione"
                onChange={(e) => setUseSmartGeneration(e.target.value === 'smart')}
              >
                <MenuItem value="smart">🧠 Generazione Intelligente (Consigliata)</MenuItem>
                <MenuItem value="standard">⚡ Generazione Standard</MenuItem>
              </Select>
            </FormControl>
          </Box>

          {/* Smart Analysis Results */}
          {useSmartGeneration && file && (
            <Box sx={{ mb: 3 }}>
              {analyzing ? (
                <Paper sx={{ p: 3, textAlign: 'center' }}>
                  <CircularProgress size={32} sx={{ mb: 2 }} />
                  <Typography variant="body1" gutterBottom>
                    Analizzando i requisiti del progetto...
                  </Typography>
                  <LinearProgress sx={{ mt: 2 }} />
                </Paper>
              ) : analysis ? (
                <Fade in={true}>
                  <Paper sx={{ p: 3, bgcolor: 'background.default' }}>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <PsychologyIcon color="primary" />
                      Analisi Intelligente Completata
                    </Typography>
                    
                    <Grid container spacing={2} sx={{ mb: 2 }}>
                      <Grid item xs={6} sm={3}>
                        <Box sx={{ textAlign: 'center' }}>
                          <Typography variant="caption" color="text.secondary">
                            Tipo Progetto
                          </Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {analysis.project_type}
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Box sx={{ textAlign: 'center' }}>
                          <Typography variant="caption" color="text.secondary">
                            Complessità
                          </Typography>
                          <Chip 
                            label={analysis.complexity} 
                            color={getComplexityColor(analysis.complexity)}
                            size="small"
                          />
                        </Box>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Box sx={{ textAlign: 'center' }}>
                          <Typography variant="caption" color="text.secondary">
                            File Stimati
                          </Typography>
                          <Typography variant="body2" fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                            <FolderIcon fontSize="small" />
                            {analysis.estimated_files.total}
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Box sx={{ textAlign: 'center' }}>
                          <Typography variant="caption" color="text.secondary">
                            Durata Stimata
                          </Typography>
                          <Typography variant="body2" fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                            <TimerIcon fontSize="small" />
                            {analysis.estimated_duration}
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>

                    {analysis.features_detected && analysis.features_detected.length > 0 && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Features Rilevate:
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {analysis.features_detected.map((feature: string, index: number) => (
                            <Chip 
                              key={index} 
                              label={feature.replace('_', ' ')}
                              variant="outlined" 
                              size="small" 
                            />
                          ))}
                        </Box>
                      </Box>
                    )}

                    <Alert severity="info" sx={{ mb: 2 }}>
                      <AlertTitle>Strategia Consigliata</AlertTitle>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        {getAgentIcon(analysis.agent_mode)}
                        <Typography variant="body2" fontWeight="bold">
                          {analysis.agent_mode.replace('_', ' ').toUpperCase()}
                        </Typography>
                        <Chip label={`${analysis.max_iterations} iterazioni`} size="small" />
                      </Box>
                      <Typography variant="body2">
                        {analysis.reasoning && analysis.reasoning.length > 0 
                          ? analysis.reasoning.slice(0, 2).join('. ') + '.'
                          : 'Sistema ottimale per questo tipo di progetto.'}
                      </Typography>
                    </Alert>

                    {/* Advanced Options */}
                    {agentModes && (
                      <Accordion expanded={showAdvanced} onChange={() => setShowAdvanced(!showAdvanced)}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Typography variant="body2" fontWeight="medium">
                            Opzioni Avanzate (Opzionale)
                          </Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Box sx={{ mb: 2 }}>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                              Modalità Agente Override:
                            </Typography>
                            <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                              <Select
                                value={selectedAgentMode}
                                onChange={(e) => setSelectedAgentMode(e.target.value)}
                              >
                                {agentModes.agent_modes.map((mode: any) => (
                                  <MenuItem key={mode.id} value={mode.id}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                      {getAgentIcon(mode.id)}
                                      <Box>
                                        <Typography variant="body2" fontWeight="medium">
                                          {mode.name}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary">
                                          {mode.avg_duration} • {mode.typical_files}
                                        </Typography>
                                      </Box>
                                    </Box>
                                  </MenuItem>
                                ))}
                              </Select>
                            </FormControl>

                            <Typography variant="body2" color="text.secondary" gutterBottom>
                              Iterazioni Massime: {selectedMaxIterations}
                            </Typography>
                            <Box sx={{ px: 1 }}>
                              <input
                                type="range"
                                min="1"
                                max="20"
                                value={selectedMaxIterations}
                                onChange={(e) => setSelectedMaxIterations(parseInt(e.target.value))}
                                style={{ width: '100%' }}
                              />
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                                <Typography variant="caption" color="text.secondary">1 (Veloce)</Typography>
                                <Typography variant="caption" color="text.secondary">20 (Completo)</Typography>
                              </Box>
                            </Box>
                          </Box>
                        </AccordionDetails>
                      </Accordion>
                    )}
                  </Paper>
                </Fade>
              ) : null}
            </Box>
          )}

          {/* Standard Generation Info */}
          {!useSmartGeneration && (
            <Alert severity="info" sx={{ mb: 2 }}>
              <AlertTitle>Generazione Standard</AlertTitle>
              Verrà utilizzato il sistema multi-agente standard con 10 iterazioni massime.
              La generazione intelligente può ottimizzare automaticamente questo processo.
            </Alert>
          )}

          {/* Info Box */}
          <Paper sx={{ p: 2, bgcolor: 'grey.50', border: 1, borderColor: 'grey.200' }}>
            <Typography variant="body2" color="text.primary">
              <strong>Cosa succederà:</strong>
            </Typography>
            <Box component="ul" sx={{ mt: 1, mb: 0, pl: 2 }}>
              <li>
                <Typography variant="body2">
                  Il file verrà caricato e analizzato
                  {useSmartGeneration && analysis && (
                    <> (Analisi: {analysis.complexity} complexity, {analysis.estimated_files.total} files)</>
                  )}
                </Typography>
              </li>
              <li>
                <Typography variant="body2">
                  {useSmartGeneration && analysis ? (
                    <>Verrà utilizzato il sistema <strong>{analysis.agent_mode.replace('_', ' ')}</strong> con {selectedMaxIterations} iterazioni</>
                  ) : (
                    <>L'AI inizierà a generare il codice (fino a 10 iterazioni)</>
                  )}
                </Typography>
              </li>
              <li>
                <Typography variant="body2">
                  Il progresso verrà monitorato automaticamente
                  {useSmartGeneration && analysis && (
                    <> (Durata stimata: {analysis.estimated_duration})</>
                  )}
                </Typography>
              </li>
              <li>
                <Typography variant="body2">
                  Potrai scaricare il progetto quando completato
                </Typography>
              </li>
            </Box>
          </Paper>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Annulla
        </Button>
        <Button 
          onClick={handleSubmit} 
          variant="contained"
          disabled={!file || loading || !projectName.trim() || analyzing}
          startIcon={loading ? <CircularProgress size={16} /> : <AutorenewIcon />}
          sx={{
            bgcolor: useSmartGeneration ? 'primary.main' : 'secondary.main',
            '&:hover': {
              bgcolor: useSmartGeneration ? 'primary.dark' : 'secondary.dark',
            }
          }}
        >
          {loading ? 'Creazione in corso...' : 
           analyzing ? 'Analizzando...' :
           useSmartGeneration ? 'Crea con AI Intelligente' : 'Crea Progetto Standard'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CreateProjectDialog;