// ImportProjectDialog.tsx - Versione completa
import React, { useState, useRef } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Tabs,
  Tab,
  Box,
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
  InputAdornment,
  IconButton,
  Tooltip,
  CircularProgress
} from '@mui/material';
import {
  Upload as UploadIcon,
  GitHub as GitHubIcon,
  FolderZip as ZipIcon,
  Visibility as PreviewIcon,
  Info as InfoIcon,
  Close as CloseIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import CodeGeneratorAPI from '../src/services/api';

interface ImportProjectDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: (projectData: any) => void;
  loading: boolean;
  api: CodeGeneratorAPI;
}

interface ImportResult {
  project_id: string;
  project_name: string;
  imported_files: string[];
  analysis?: any;
}

interface GitHubFormData {
  repo_url: string;
  branch: string;
  name: string;
  description: string;
  access_token: string;
}

const ImportProjectDialog: React.FC<ImportProjectDialogProps> = ({
  open,
  onClose,
  onSuccess,
  loading,
  api
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState<string>('');
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);

  // File import state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileImportName, setFileImportName] = useState('');
  const [fileImportDescription, setFileImportDescription] = useState('');
  const [overwriteExisting, setOverwriteExisting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // GitHub import state
  const [githubForm, setGithubForm] = useState<GitHubFormData>({
    repo_url: '',
    branch: 'main',
    name: '',
    description: '',
    access_token: ''
  });

  const [showTokenField, setShowTokenField] = useState(false);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
    setError('');
    setImportResult(null);
    setAnalysis(null);
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      
      // Auto-generate name from filename
      const nameWithoutExt = file.name.replace(/\.(zip|tar|tar\.gz)$/i, '');
      setFileImportName(nameWithoutExt);
      setError('');
    }
  };

  const handleGithubFormChange = (field: keyof GitHubFormData, value: string) => {
    setGithubForm(prev => ({ ...prev, [field]: value }));
    
    // Auto-generate name from repo URL
    if (field === 'repo_url' && value) {
      const repoName = value.split('/').pop()?.replace('.git', '') || '';
      setGithubForm(prev => ({ ...prev, name: repoName }));
    }
    
    setError('');
  };

  const validateGithubUrl = (url: string): boolean => {
    const githubPattern = /^https:\/\/github\.com\/[\w\-\.]+\/[\w\-\.]+(?:\.git)?$/;
    return githubPattern.test(url);
  };

  const handleFileImport = async () => {
    if (!selectedFile) {
      setError('Seleziona un file da importare');
      return;
    }

    setImporting(true);
    setError('');

    try {
      // Simuliamo l'importazione (in attesa degli endpoint reali)
      // Questo andrebbe sostituito con una vera chiamata API quando implementata

      // Simula ritardo di importazione
      await new Promise(resolve => setTimeout(resolve, 1500));

      const mockResult = {
        project_id: `import_${Date.now()}`,
        project_name: fileImportName || selectedFile.name.replace(/\.(zip|tar|tar\.gz)$/i, ''),
        imported_files: ['src/index.js', 'src/App.js', 'package.json', 'README.md', '.gitignore'],
        status: 'imported'
      };

      setImportResult(mockResult);
      
      // Simuliamo l'analisi
      setAnalyzing(true);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockAnalysis = {
        technologies: ['React', 'JavaScript', 'CSS', 'HTML', 'Node.js'],
        estimated_complexity: 'medium',
        suggestions: [
          'Considerare l\'aggiunta di test unitari',
          'Il progetto potrebbe beneficiare di TypeScript',
          'Aggiornare le dipendenze obsolete'
        ]
      };
      
      setAnalysis(mockAnalysis);
      setAnalyzing(false);

    } catch (error: any) {
      setError(error.message || 'Errore durante l\'importazione');
    } finally {
      setImporting(false);
    }
  };

  const handleGithubImport = async () => {
    if (!githubForm.repo_url) {
      setError('Inserisci l\'URL del repository');
      return;
    }

    if (!validateGithubUrl(githubForm.repo_url)) {
      setError('URL GitHub non valido');
      return;
    }

    setImporting(true);
    setError('');

    try {
      // Simuliamo l'importazione da GitHub (in attesa degli endpoint reali)
      // Questo andrebbe sostituito con una vera chiamata API quando implementata

      // Simula ritardo di importazione
      await new Promise(resolve => setTimeout(resolve, 2000));

      const repoName = githubForm.repo_url.split('/').pop()?.replace('.git', '') || '';
      
      const mockResult = {
        project_id: `github_${Date.now()}`,
        project_name: githubForm.name || repoName,
        imported_files: ['src/index.js', 'src/components/App.js', 'package.json', 'README.md', '.github/workflows/ci.yml'],
        status: 'imported'
      };

      setImportResult(mockResult);
      
      // Simuliamo l'analisi
      setAnalyzing(true);
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const mockAnalysis = {
        technologies: ['React', 'JavaScript', 'Redux', 'SCSS', 'Jest'],
        estimated_complexity: 'high',
        suggestions: [
          'La struttura del codice è ben organizzata',
          'Considerare l\'implementazione di una strategia di caching',
          'Migliorare la gestione degli errori'
        ]
      };
      
      setAnalysis(mockAnalysis);
      setAnalyzing(false);

    } catch (error: any) {
      setError(error.message || 'Errore durante l\'importazione da GitHub');
      
      // Suggerisci di usare un token per repo privati
      if (error.message && (error.message.includes('404') || error.message.includes('private'))) {
        setShowTokenField(true);
        setError(error.message + '. Se il repository è privato, aggiungi un access token.');
      }
    } finally {
      setImporting(false);
    }
  };

  const handleConfirmImport = () => {
    if (importResult) {
      onSuccess({
        project_id: importResult.project_id,
        project_name: importResult.project_name,
        status: 'imported',
        created_at: new Date().toISOString(),
        imported_files: importResult.imported_files,
        analysis: analysis
      });
      handleClose();
    }
  };

  const handleClose = () => {
    setActiveTab(0);
    setSelectedFile(null);
    setFileImportName('');
    setFileImportDescription('');
    setOverwriteExisting(false);
    setGithubForm({
      repo_url: '',
      branch: 'main',
      name: '',
      description: '',
      access_token: ''
    });
    setShowTokenField(false);
    setError('');
    setImportResult(null);
    setAnalysis(null);
    setImporting(false);
    setAnalyzing(false);
    onClose();
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'low': return 'success';
      case 'medium': return 'warning';
      case 'high': return 'error';
      default: return 'default';
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: '60vh' }
      }}
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h6">
          Importa Progetto Esistente
        </Typography>
        <IconButton onClick={handleClose} disabled={importing || loading}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent>
        {!importResult ? (
          <>
            <Tabs value={activeTab} onChange={handleTabChange} sx={{ mb: 3 }}>
              <Tab icon={<ZipIcon />} label="Da File" />
              <Tab icon={<GitHubIcon />} label="Da GitHub" />
            </Tabs>

            {/* File Import Tab */}
            {activeTab === 0 && (
              <Box>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Importa un progetto esistente da un file ZIP, TAR o TAR.GZ
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
                        accept=".zip,.tar,.tar.gz,.tgz"
                        onChange={handleFileSelect}
                        style={{ display: 'none' }}
                      />
                      
                      <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                      
                      {selectedFile ? (
                        <Box>
                          <Typography variant="h6" gutterBottom>
                            {selectedFile.name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                          </Typography>
                        </Box>
                      ) : (
                        <Box>
                          <Typography variant="h6" gutterBottom>
                            Clicca per selezionare un file
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Formati supportati: ZIP, TAR, TAR.GZ
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  </CardContent>
                </Card>

                <TextField
                  fullWidth
                  label="Nome progetto"
                  value={fileImportName}
                  onChange={(e) => setFileImportName(e.target.value)}
                  margin="normal"
                  helperText="Lascia vuoto per usare il nome del file"
                />

                <TextField
                  fullWidth
                  label="Descrizione (opzionale)"
                  value={fileImportDescription}
                  onChange={(e) => setFileImportDescription(e.target.value)}
                  margin="normal"
                  multiline
                  rows={2}
                />

                <FormControlLabel
                  control={
                    <Switch
                      checked={overwriteExisting}
                      onChange={(e) => setOverwriteExisting(e.target.checked)}
                    />
                  }
                  label="Sovrascrivi se esiste già"
                  sx={{ mt: 1 }}
                />
              </Box>
            )}

            {/* GitHub Import Tab */}
            {activeTab === 1 && (
              <Box>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Importa un progetto direttamente da un repository GitHub
                </Typography>

                <TextField
                  fullWidth
                  label="URL Repository GitHub"
                  value={githubForm.repo_url}
                  onChange={(e) => handleGithubFormChange('repo_url', e.target.value)}
                  margin="normal"
                  placeholder="https://github.com/utente/repository"
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <GitHubIcon />
                      </InputAdornment>
                    )
                  }}
                  error={githubForm.repo_url !== '' && !validateGithubUrl(githubForm.repo_url)}
                  helperText={
                    githubForm.repo_url !== '' && !validateGithubUrl(githubForm.repo_url)
                      ? 'URL GitHub non valido'
                      : 'Repository pubblici o privati (con token)'
                  }
                />

                <Box sx={{ display: 'flex', gap: 2 }}>
                  <TextField
                    label="Branch"
                    value={githubForm.branch}
                    onChange={(e) => handleGithubFormChange('branch', e.target.value)}
                    margin="normal"
                    sx={{ flex: 1 }}
                  />
                  
                  <TextField
                    label="Nome progetto"
                    value={githubForm.name}
                    onChange={(e) => handleGithubFormChange('name', e.target.value)}
                    margin="normal"
                    sx={{ flex: 1 }}
                    helperText="Auto-generato dall'URL"
                  />
                </Box>

                <TextField
                  fullWidth
                  label="Descrizione (opzionale)"
                  value={githubForm.description}
                  onChange={(e) => handleGithubFormChange('description', e.target.value)}
                  margin="normal"
                  multiline
                  rows={2}
                />

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={showTokenField}
                        onChange={(e) => setShowTokenField(e.target.checked)}
                      />
                    }
                    label="Repository privato"
                  />
                  <Tooltip title="Necessario per repository privati o per evitare rate limiting">
                    <InfoIcon color="action" />
                  </Tooltip>
                </Box>

                {showTokenField && (
                  <TextField
                    fullWidth
                    type="password"
                    label="GitHub Access Token"
                    value={githubForm.access_token}
                    onChange={(e) => handleGithubFormChange('access_token', e.target.value)}
                    margin="normal"
                    helperText="Token per repository privati (Settings > Developer settings > Personal access tokens)"
                  />
                )}
              </Box>
            )}

            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}

            {importing && (
              <Box sx={{ mt: 2 }}>
                <LinearProgress />
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Importazione in corso...
                </Typography>
              </Box>
            )}
          </>
        ) : (
          /* Import Success/Analysis View */
          <Box>
            <Alert severity="success" sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Progetto importato con successo!
              </Typography>
              <Typography variant="body2">
                Il progetto "{importResult.project_name}" è stato importato correttamente.
              </Typography>
            </Alert>

            <Card variant="outlined" sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Dettagli Importazione
                </Typography>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Nome progetto
                  </Typography>
                  <Typography variant="body1" fontWeight={500}>
                    {importResult.project_name}
                  </Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    File importati
                  </Typography>
                  <Typography variant="body1">
                    {importResult.imported_files.length} file
                  </Typography>
                </Box>

                <Divider sx={{ my: 2 }} />

                {analyzing ? (
                  <Box sx={{ textAlign: 'center' }}>
                    <CircularProgress size={40} />
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      Analisi del progetto in corso...
                    </Typography>
                  </Box>
                ) : analysis ? (
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      Analisi del Progetto
                    </Typography>

                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Complessità stimata
                      </Typography>
                      <Chip
                        label={analysis.estimated_complexity.toUpperCase()}
                        color={getComplexityColor(analysis.estimated_complexity)}
                        variant="outlined"
                      />
                    </Box>

                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Tecnologie rilevate
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {analysis.technologies.map((tech: string, index: number) => (
                          <Chip 
                            key={index} 
                            label={tech} 
                            size="small" 
                            variant="outlined"
                          />
                        ))}
                      </Box>
                    </Box>

                    {analysis.suggestions && analysis.suggestions.length > 0 && (
                      <Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Suggerimenti
                        </Typography>
                        <Box component="ul" sx={{ mt: 0, pl: 2 }}>
                          {analysis.suggestions.map((suggestion: string, index: number) => (
                            <li key={index}>
                              <Typography variant="body2">{suggestion}</Typography>
                            </li>
                          ))}
                        </Box>
                      </Box>
                    )}
                  </Box>
                ) : (
                  <Typography color="text.secondary">
                    Analisi non disponibile
                  </Typography>
                )}
              </CardContent>
            </Card>

            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              <Typography variant="body2" color="text.secondary">
                File principali:
              </Typography>
              {importResult.imported_files
                .filter(file => 
                  file.includes('index.') || 
                  file.includes('package.json') || 
                  file.includes('requirements.') ||
                  file.includes('main.') ||
                  file.includes('app.') ||
                  file.endsWith('.csproj') ||
                  file.endsWith('.sln')
                )
                .slice(0, 5)
                .map((file, index) => (
                  <Chip key={index} label={file} size="small" />
                ))}
            </Box>
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        {!importResult ? (
          <>
            <Button onClick={handleClose} disabled={importing || loading}>
              Annulla
            </Button>
            {activeTab === 0 ? (
              <Button
                onClick={handleFileImport}
                variant="contained"
                disabled={!selectedFile || importing || loading}
                startIcon={<UploadIcon />}
              >
                Importa File
              </Button>
            ) : (
              <Button
                onClick={handleGithubImport}
                variant="contained"
                disabled={!githubForm.repo_url || importing || loading}
                startIcon={<GitHubIcon />}
              >
                Importa da GitHub
              </Button>
            )}
          </>
        ) : (
          <>
            <Button
              onClick={handleClose}
              color="inherit"
              disabled={loading}
            >
              Chiudi
            </Button>
            <Button
              onClick={handleConfirmImport}
              variant="contained"
              color="primary"
              disabled={loading}
            >
              Apri Progetto
            </Button>
          </>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default ImportProjectDialog;