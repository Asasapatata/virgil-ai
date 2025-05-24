// StopGenerationButton.tsx - Versione corretta e completa
import React, { useState, useEffect } from 'react';
import {
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  CircularProgress,
  Alert,
  Box,
  SxProps, 
  Theme
} from '@mui/material';
import {
  Stop as StopIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
import CodeGeneratorAPI from '../src/services/api';

interface StopGenerationButtonProps {
  projectId: string;
  projectName: string;
  onStopSuccess: () => void;
  onError: (error: Error) => void;
  api: CodeGeneratorAPI;
  disabled?: boolean;
  sx?: SxProps<Theme>;
  'data-stop-generation'?: string;
}

const StopGenerationButton: React.FC<StopGenerationButtonProps> = ({
  projectId,
  projectName,
  onStopSuccess,
  onError,
  api,
  disabled = false,
  sx,
  'data-stop-generation': dataStopGeneration
}) => {
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [canStop, setCanStop] = useState<{ can_stop: boolean; reason?: string }>({ 
    can_stop: true // Default a true per questa demo
  });
  const [checkingStatus, setCheckingStatus] = useState(true);

  // Controlla se la generazione può essere fermata
  useEffect(() => {
    const checkCanStop = async () => {
      if (disabled) {
        setCheckingStatus(false);
        return;
      }

      try {
        setCheckingStatus(true);
        
        try {
          // Prova a verificare dal backend
          const result = await api.canStopGeneration(projectId);
          setCanStop(result);
        } catch (error) {
          console.warn('Error checking stop capability, assuming can stop:', error);
          // Fallback: assumiamo che possa essere fermato
          setCanStop({ 
            can_stop: true,
            reason: "La generazione è in corso e può essere fermata" 
          });
        }
      } catch (error) {
        console.error('Error in checkCanStop:', error);
        setCanStop({ can_stop: false, reason: 'Impossibile verificare stato' });
      } finally {
        setCheckingStatus(false);
      }
    };

    checkCanStop();
    
    // Check periodicamente
    const interval = setInterval(checkCanStop, 10000); // ogni 10 secondi
    return () => clearInterval(interval);
  }, [api, projectId, disabled]);

  const handleStopClick = () => {
    setShowConfirmDialog(true);
  };

  const handleConfirmStop = async () => {
    setStopping(true);
    setShowConfirmDialog(false);

    try {
      console.log('Tentativo di fermare la generazione per il progetto:', projectId);
      
      // Assicuriamoci che api.stopGeneration sia una funzione prima di chiamarla
      if (typeof api.stopGeneration !== 'function') {
        throw new Error('stopGeneration non è una funzione disponibile nell\'API');
      }
      
      // Chiamata al backend per fermare la generazione
      const result = await api.stopGeneration(projectId);
      
      console.log('Risultato stop generation:', result);
      
      if (result && result.success !== false) {
        onStopSuccess();
      } else {
        throw new Error(result?.message || 'Stop failed without specific error');
      }
    } catch (error) {
      console.error('Error stopping generation:', error);
      onError(error instanceof Error ? error : new Error(String(error)));
    } finally {
      setStopping(false);
    }
  };

  const handleCancelStop = () => {
    setShowConfirmDialog(false);
  };

  // Non renderizza se sta controllando lo stato
  if (checkingStatus) {
    return (
      <Button
        variant="outlined"
        color="warning"
        disabled
        startIcon={<CircularProgress size={20} />}
        sx={{ minWidth: 120, ...sx }}
        data-stop-generation={dataStopGeneration}
      >
        Verifica...
      </Button>
    );
  }

  // Non renderizza se non può fermare
  if (!canStop.can_stop) {
    return null;
  }

  return (
    <>
      <Button
        variant="outlined"
        color="warning"
        onClick={handleStopClick}
        disabled={disabled || stopping}
        startIcon={stopping ? <CircularProgress size={20} /> : <StopIcon />}
        sx={{ 
          minWidth: 120,
          borderColor: 'warning.main',
          color: 'warning.main',
          '&:hover': {
            borderColor: 'warning.dark',
            backgroundColor: 'warning.lighter'
          },
          ...sx
        }}
        data-stop-generation={dataStopGeneration}
      >
        {stopping ? 'Fermando...' : 'Ferma Generazione'}
      </Button>

      {/* Confirmation Dialog */}
      <Dialog
        open={showConfirmDialog}
        onClose={handleCancelStop}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <WarningIcon color="warning" />
          Ferma Generazione
        </DialogTitle>
        
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Attenzione: Operazione irreversibile
            </Typography>
            <Typography variant="body2">
              Fermando la generazione ora perderai tutto il progresso dell'iterazione corrente.
            </Typography>
          </Alert>

          <Typography variant="body2" color="text.secondary" paragraph>
            Stai per fermare la generazione per il progetto <strong>"{projectName}"</strong>.
          </Typography>

          <Box sx={{ bgcolor: 'background.paper', p: 2, borderRadius: 1, border: 1, borderColor: 'divider' }}>
            <Typography variant="subtitle2" gutterBottom>
              Cosa succederà:
            </Typography>
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              <li>
                <Typography variant="body2">
                  Il task di generazione verrà cancellato
                </Typography>
              </li>
              <li>
                <Typography variant="body2">
                  Lo stato del progetto cambierà in "Fermato"
                </Typography>
              </li>
              <li>
                <Typography variant="body2">
                  Dovrai riavviare manualmente la generazione
                </Typography>
              </li>
              <li>
                <Typography variant="body2">
                  I file dell'iterazione corrente potrebbero essere incompleti
                </Typography>
              </li>
            </ul>
          </Box>

          {canStop.reason && (
            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="body2">
                <strong>Nota:</strong> {canStop.reason}
              </Typography>
            </Alert>
          )}
        </DialogContent>

        <DialogActions>
          <Button onClick={handleCancelStop} color="primary">
            Annulla
          </Button>
          <Button 
            onClick={handleConfirmStop}
            color="warning" 
            variant="contained"
            startIcon={<StopIcon />}
          >
            Ferma Generazione
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default StopGenerationButton;