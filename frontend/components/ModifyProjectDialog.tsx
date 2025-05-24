// ModifyProjectDialog.tsx - Versione corretta con tipi appropriati
import React, { useState, useRef, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Alert,
  LinearProgress,
  Card,
  CardContent,
  Chip,
  Divider,
  FormControlLabel,
  Switch,
  Box,
  RadioGroup,
  Radio,
  FormControl,
  FormLabel,
  Stepper,
  Step,
  StepLabel,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Tooltip,
  CircularProgress
} from '@mui/material';
import {
  Upload as UploadIcon,
  FilePresent as FileIcon,
  Add as AddIcon,
  Remove as RemoveIcon,
  Edit as EditIcon,
  Preview as PreviewIcon,
  ArrowForward as ArrowForwardIcon,
  Warning as WarningIcon,
  Close as CloseIcon,
  Code as CodeIcon,
  Check as CheckIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import CodeGeneratorAPI from '../src/services/api';

interface ProjectMinimal {
  project_id: string;
  project_name: string;
}

interface ModifyProjectDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: (modificationData: any) => void;
  project: ProjectMinimal;
  loading: boolean;
  api: CodeGeneratorAPI; // Corretto: usare il tipo specifico invece di any
}

interface ModificationResult {
  task_id: string;
  modification_id: string;
  estimated_changes: string[];
}

interface FileChange {
  file: string;
  change_type: 'create' | 'modify' | 'delete';
  description: string;
  impact: 'low' | 'medium' | 'high';
}

interface PreviewResult {
  estimated_changes: FileChange[];
  risks: string[];
  recommendations: string[];
}

const ModifyProjectDialog: React.FC<ModifyProjectDialogProps> = ({
  open,
  onClose,
  onSuccess,
  project,
  loading,
  api
}) => {
  // Resto del codice invariato...
  const [activeStep, setActiveStep] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [description, setDescription] = useState('');
  const [modificationMode, setModificationMode] = useState<'incremental' | 'complete_rewrite'>('incremental');
  const [preserveExisting, setPreserveExisting] = useState(true);
  const [preview, setPreview] = useState<PreviewResult | null>(null);
  const [error, setError] = useState<string>('');
  const [processing, setProcessing] = useState(false);
  const [modificationResult, setModificationResult] = useState<ModificationResult | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Reset state when dialog opens
  useEffect(() => {
    if (open) {
      setActiveStep(0);
      setSelectedFile(null);
      setDescription('');
      setModificationMode('incremental');
      setPreserveExisting(true);
      setPreview(null);
      setError('');
      setProcessing(false);
      setModificationResult(null);
    }
  }, [open]);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError('');
    }
  };

  const handleNext = () => {
    if (activeStep === 0 && !selectedFile) {
      setError('Seleziona un file di requisiti');
      return;
    }
    
    if (activeStep === 1) {
      // Perform preview
      handlePreviewModifications();
      return;
    }
    
    if (activeStep === 2) {
      // Start modification
      handleStartModification();
      return;
    }
    
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
    setError('');
  };

  const handlePreviewModifications = async () => {
    if (!selectedFile) {
      setError('Seleziona un file di requisiti');
      return;
    }

    setProcessing(true);
    setError('');

    try {
      // Simulazione della preview (sostituire con API reale quando pronta)
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const mockPreview: PreviewResult = {
        estimated_changes: [
          {
            file: 'src/components/Header.js',
            change_type: 'modify',
            description: 'Aggiunta funzionalità di ricerca nella navbar',
            impact: 'medium'
          },
          {
            file: 'src/components/SearchBar.js',
            change_type: 'create',
            description: 'Nuovo componente per la ricerca',
            impact: 'low'
          },
          {
            file: 'src/styles/theme.js',
            change_type: 'modify',
            description: 'Aggiornamento colori e stili per il tema dark',
            impact: 'low'
          },
          {
            file: 'src/components/Sidebar.js',
            change_type: 'modify',
            description: 'Nuova struttura di navigazione con categorie',
            impact: 'high'
          }
        ],
        risks: [
          'Modifiche alla navigazione potrebbero influenzare l\'usabilità esistente',
          'L\'implementazione del tema dark richiede test approfonditi di accessibilità'
        ],
        recommendations: [
          'Aggiungere test per le nuove funzionalità di ricerca',
          'Verificare la compatibilità con browser meno recenti',
          'Considerare l\'aggiunta di documentazione per i nuovi componenti'
        ]
      };
      
      setPreview(mockPreview);
      setActiveStep(2);
    } catch (error: any) {
      setError(error.message || 'Errore durante la generazione dell\'anteprima');
    } finally {
      setProcessing(false);
    }
  };

  const handleStartModification = async () => {
    if (!selectedFile) {
      setError('Seleziona un file di requisiti');
      return;
    }

    setProcessing(true);
    setError('');

    try {
      // Simulazione dell'avvio della modifica (sostituire con API reale quando pronta)
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const mockResult: ModificationResult = {
        task_id: `task_${Date.now()}`,
        modification_id: `mod_${Date.now()}`,
        estimated_changes: preview?.estimated_changes.map(change => change.file) || []
      };
      
      setModificationResult(mockResult);
      setActiveStep(3);
    } catch (error: any) {
      setError(error.message || 'Errore durante l\'avvio della modifica');
    } finally {
      setProcessing(false);
    }
  };

  const handleConfirm = () => {
    if (modificationResult) {
      onSuccess({
        project_id: project.project_id,
        modification_id: modificationResult.modification_id,
        task_id: modificationResult.task_id,
        mode: modificationMode,
        estimated_changes: modificationResult.estimated_changes
      });
      handleClose();
    }
  };

  const handleClose = () => {
    setActiveStep(0);
    setSelectedFile(null);
    setDescription('');
    setModificationMode('incremental');
    setPreserveExisting(true);
    setPreview(null);
    setError('');
    setProcessing(false);
    setModificationResult(null);
    onClose();
  };

  const getStepContent = (step: number) => {
    // Implementazione esistente
    // ...
    switch (step) {
      case 0:
        return (
          <>
            <Typography variant="h6" gutterBottom>
              Seleziona File di Requisiti
            </Typography>
            
            <Typography variant="body2" color="text.secondary" paragraph>
              Carica un file YAML con le nuove specifiche o requisiti per modificare il progetto.
            </Typography>
            
            <Card variant="outlined" sx={{ mb: 3 }}>
              <CardContent>
                <Box
                  sx={{
                    border: '2px dashed',
                    borderColor: selectedFile ? 'primary.main' : 'grey.300',
                    borderRadius: 2,
                    p: 3,
                    textAlign: 'center',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    '&:hover': {
                      borderColor: 'primary.main',
                      bgcolor: 'action.hover'
                    }
                  }}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".yaml,.yml"
                    onChange={handleFileSelect}
                    style={{ display: 'none' }}
                  />
                  
                  <FileIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                  
                  {selectedFile ? (
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        {selectedFile.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {(selectedFile.size / 1024).toFixed(2)} KB
                      </Typography>
                    </Box>
                  ) : (
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        Clicca per selezionare un file
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Formati supportati: YAML, YML
                      </Typography>
                    </Box>
                  )}
                </Box>
              </CardContent>
            </Card>
            
            <TextField
              fullWidth
              label="Descrizione della modifica (opzionale)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              margin="normal"
              multiline
              rows={2}
              placeholder="Descrivi brevemente le modifiche che stai apportando..."
            />
          </>
        );
      
      case 1:
        return (
          <>
            <Typography variant="h6" gutterBottom>
              Configurazione della Modifica
            </Typography>
            
            <Typography variant="body2" color="text.secondary" paragraph>
              Imposta come vuoi che il progetto venga modificato.
            </Typography>
            
            <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
              <FormControl component="fieldset" sx={{ mb: 3 }}>
                <FormLabel component="legend">
                  <Typography variant="subtitle2">Modalità di modifica</Typography>
                </FormLabel>
                <RadioGroup
                  value={modificationMode}
                  onChange={(e) => setModificationMode(e.target.value as 'incremental' | 'complete_rewrite')}
                >
                  <FormControlLabel
                    value="incremental"
                    control={<Radio />}
                    label={
                      <Box>
                        <Typography variant="body2">Incrementale</Typography>
                        <Typography variant="caption" color="text.secondary">
                          Modifiche mirate basate sui requisiti, preservando la struttura esistente
                        </Typography>
                      </Box>
                    }
                  />
                  <FormControlLabel
                    value="complete_rewrite"
                    control={<Radio />}
                    label={
                      <Box>
                        <Typography variant="body2">Riscrittura completa</Typography>
                        <Typography variant="caption" color="text.secondary">
                          Rigenera interamente il progetto sulla base dei nuovi requisiti
                        </Typography>
                      </Box>
                    }
                  />
                </RadioGroup>
              </FormControl>
              
              <Divider sx={{ my: 2 }} />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={preserveExisting}
                    onChange={(e) => setPreserveExisting(e.target.checked)}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">Preserva file esistenti</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Mantieni i file che non vengono esplicitamente modificati dai nuovi requisiti
                    </Typography>
                  </Box>
                }
              />
            </Paper>
            
            <Alert severity="info" icon={<InfoIcon />}>
              <Typography variant="subtitle2" gutterBottom>
                Informazioni importanti
              </Typography>
              <Typography variant="body2">
                La generazione di modifiche ad un progetto esistente potrebbe richiedere diversi minuti.
                Verifica che i requisiti siano chiari per ottenere i migliori risultati.
              </Typography>
            </Alert>
          </>
        );
      
      case 2:
        return (
          <>
            <Typography variant="h6" gutterBottom>
              Anteprima delle Modifiche
            </Typography>
            
            {!preview ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                {processing ? (
                  <>
                    <CircularProgress size={40} />
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                      Generazione anteprima in corso...
                    </Typography>
                  </>
                ) : (
                  <>
                    <PreviewIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                    <Typography variant="body1">
                      Clicca "Genera Anteprima" per visualizzare le modifiche stimate
                    </Typography>
                  </>
                )}
              </Box>
            ) : (
              <>
                <Card variant="outlined" sx={{ mb: 3 }}>
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      Modifiche previste:
                    </Typography>
                    
                    <List dense>
                      {preview.estimated_changes.map((change, index) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            {change.change_type === 'create' ? (
                              <AddIcon color="success" />
                            ) : change.change_type === 'modify' ? (
                              <EditIcon color="primary" />
                            ) : (
                              <RemoveIcon color="error" />
                            )}
                          </ListItemIcon>
                          <ListItemText
                            primary={change.file}
                            secondary={change.description}
                          />
                          <Chip
                            size="small"
                            label={change.impact.toUpperCase()}
                            color={
                              change.impact === 'high' 
                                ? 'error' 
                                : change.impact === 'medium' 
                                ? 'warning' 
                                : 'success'
                            }
                            variant="outlined"
                          />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
                
                {preview.risks && preview.risks.length > 0 && (
                  <Alert severity="warning" sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Rischi potenziali
                    </Typography>
                    <Box component="ul" sx={{ mt: 0, pl: 2 }}>
                      {preview.risks.map((risk, index) => (
                        <li key={index}>
                          <Typography variant="body2">{risk}</Typography>
                        </li>
                      ))}
                    </Box>
                  </Alert>
                )}
                
                {preview.recommendations && preview.recommendations.length > 0 && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Raccomandazioni
                    </Typography>
                    <Box component="ul" sx={{ mt: 0, pl: 2 }}>
                      {preview.recommendations.map((rec, index) => (
                        <li key={index}>
                          <Typography variant="body2">{rec}</Typography>
                        </li>
                      ))}
                    </Box>
                  </Box>
                )}
              </>
            )}
          </>
        );
        
      case 3:
        return (
          <>
            <Alert severity="success" sx={{ mb: 3 }}>
              <Typography variant="subtitle1" gutterBottom>
                Modifica avviata con successo!
              </Typography>
              <Typography variant="body2">
                La modifica del progetto è stata avviata. Il processo richiederà alcuni minuti.
              </Typography>
            </Alert>
            
            <Card variant="outlined" sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Dettagli della Modifica
                </Typography>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Progetto
                  </Typography>
                  <Typography variant="body1" fontWeight={500}>
                    {project.project_name}
                  </Typography>
                </Box>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Modalità di modifica
                  </Typography>
                  <Chip
                    label={modificationMode === 'incremental' ? 'Incrementale' : 'Riscrittura completa'}
                    color={modificationMode === 'incremental' ? 'primary' : 'warning'}
                    variant="outlined"
                    size="small"
                  />
                </Box>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    File da modificare
                  </Typography>
                  <Typography variant="body1">
                    {modificationResult?.estimated_changes.length || '?'} file
                  </Typography>
                </Box>
                
                <Divider sx={{ my: 2 }} />
                
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Il progetto verrà aggiornato automaticamente al termine dell'elaborazione.
                  Puoi monitorare lo stato dalla dashboard.
                </Typography>
              </CardContent>
            </Card>
          </>
        );
        
      default:
        return 'Passaggio sconosciuto';
    }
  };

  return (
    <Dialog
      open={open}
      onClose={(_, reason) => {
        if (reason !== 'backdropClick' || !processing) {
          handleClose();
        }
      }}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: '60vh' }
      }}
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h6">
          Modifica progetto: {project.project_name}
        </Typography>
        <IconButton onClick={handleClose} disabled={processing || loading}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent>
        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          <Step>
            <StepLabel>Requisiti</StepLabel>
          </Step>
          <Step>
            <StepLabel>Configurazione</StepLabel>
          </Step>
          <Step>
            <StepLabel>Anteprima</StepLabel>
          </Step>
          <Step>
            <StepLabel>Completamento</StepLabel>
          </Step>
        </Stepper>
        
        {getStepContent(activeStep)}
        
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
        
        {processing && activeStep !== 3 && (
          <Box sx={{ mt: 2 }}>
            <LinearProgress />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Elaborazione in corso...
            </Typography>
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        {activeStep !== 3 && (
          <Button 
            onClick={handleClose} 
            disabled={processing || loading}
          >
            Annulla
          </Button>
        )}
        
        {activeStep > 0 && activeStep < 3 && (
          <Button
            onClick={handleBack}
            disabled={processing || loading}
          >
            Indietro
          </Button>
        )}
        
        {activeStep === 3 ? (
          <Button
            onClick={handleConfirm}
            variant="contained"
            color="primary"
            disabled={loading}
          >
            Torna alla Dashboard
          </Button>
        ) : (
          <Button
            variant="contained"
            color="primary"
            onClick={handleNext}
            disabled={processing || loading || (activeStep === 0 && !selectedFile)}
            endIcon={activeStep === 1 ? <PreviewIcon /> : <ArrowForwardIcon />}
          >
            {activeStep === 0 ? 'Avanti' : 
             activeStep === 1 ? 'Genera Anteprima' : 
             activeStep === 2 ? 'Avvia Modifica' : ''}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default ModifyProjectDialog;