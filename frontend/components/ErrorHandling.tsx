import React from 'react';
import {
  Box,
  Alert,
  AlertTitle,
  Button,
  Typography,
  Chip,
  Card,
  CardContent,
  IconButton,
  Collapse,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  ContentCopy as CopyIcon,
  Close as CloseIcon
} from '@mui/icons-material';

interface ErrorDisplayProps {
  error: string | Error;
  severity?: 'error' | 'warning' | 'info';
  onRetry?: () => void;
  onDismiss?: () => void;
  showDetails?: boolean;
  context?: string;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  severity = 'error',
  onRetry,
  onDismiss,
  showDetails = false,
  context
}) => {
  const [expanded, setExpanded] = React.useState(false);
  const [copied, setCopied] = React.useState(false);

  const errorMessage = typeof error === 'string' ? error : error.message;
  const errorStack = typeof error === 'object' ? error.stack : null;

  const getErrorIcon = () => {
    switch (severity) {
      case 'warning': return <WarningIcon />;
      case 'info': return <InfoIcon />;
      default: return <ErrorIcon />;
    }
  };

  const getErrorTitle = () => {
    switch (severity) {
      case 'warning': return 'Attenzione';
      case 'info': return 'Informazione';
      default: return 'Si è verificato un errore';
    }
  };

  const copyErrorDetails = async () => {
    const details = `
Error: ${errorMessage}
Context: ${context || 'N/A'}
Timestamp: ${new Date().toISOString()}
${errorStack ? `Stack: ${errorStack}` : ''}
    `.trim();

    try {
      await navigator.clipboard.writeText(details);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy error details:', err);
    }
  };

  return (
    <Card 
      elevation={severity === 'error' ? 3 : 1}
      sx={{ 
        mb: 2,
        borderLeft: 4,
        borderLeftColor: `${severity}.main`
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
          <Box sx={{ color: `${severity}.main`, mt: 0.5 }}>
            {getErrorIcon()}
          </Box>
          
          <Box sx={{ flex: 1 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
              {getErrorTitle()}
            </Typography>
            
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {errorMessage}
            </Typography>

            {context && (
              <Chip 
                label={`Context: ${context}`} 
                size="small" 
                variant="outlined"
                sx={{ mb: 2 }}
              />
            )}

            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {onRetry && (
                <Button
                  size="small"
                  variant="contained"
                  startIcon={<RefreshIcon />}
                  onClick={onRetry}
                >
                  Riprova
                </Button>
              )}
              
              {showDetails && (
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={copied ? <InfoIcon /> : <CopyIcon />}
                  onClick={copyErrorDetails}
                  disabled={copied}
                >
                  {copied ? 'Copiato!' : 'Copia dettagli'}
                </Button>
              )}
            </Box>

            {/* Expandable error details */}
            {showDetails && errorStack && (
              <Accordion 
                expanded={expanded}
                onChange={() => setExpanded(!expanded)}
                sx={{ mt: 2, boxShadow: 'none' }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="caption">
                    Dettagli tecnici
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Box
                    sx={{
                      p: 2,
                      bgcolor: 'grey.100',
                      borderRadius: 1,
                      fontFamily: 'monospace',
                      fontSize: '0.75rem',
                      whiteSpace: 'pre-wrap',
                      overflow: 'auto',
                      maxHeight: 200
                    }}
                  >
                    {errorStack}
                  </Box>
                </AccordionDetails>
              </Accordion>
            )}
          </Box>

          {onDismiss && (
            <IconButton
              size="small"
              onClick={onDismiss}
              sx={{ color: 'text.secondary' }}
            >
              <CloseIcon />
            </IconButton>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

// Network error component
export const NetworkError: React.FC<{
  onRetry?: () => void;
  message?: string;
}> = ({ onRetry, message = "Problema di connessione" }) => (
  <ErrorDisplay
    error={message}
    severity="warning"
    onRetry={onRetry}
    context="Network"
  />
);

// Validation error component
export const ValidationError: React.FC<{
  errors: Record<string, string>;
  onDismiss?: () => void;
}> = ({ errors, onDismiss }) => (
  <Alert severity="error" onClose={onDismiss} sx={{ mb: 2 }}>
    <AlertTitle>Errori di validazione</AlertTitle>
    <Box component="ul" sx={{ mt: 1, mb: 0, pl: 2 }}>
      {Object.entries(errors).map(([field, message]) => (
        <Typography component="li" key={field} variant="body2">
          <strong>{field}:</strong> {message}
        </Typography>
      ))}
    </Box>
  </Alert>
);

// Success message with auto-dismiss
export const SuccessMessage: React.FC<{
  message: string;
  onDismiss?: () => void;
  autoHideDuration?: number;
}> = ({ message, onDismiss, autoHideDuration = 5000 }) => {
  const [open, setOpen] = React.useState(true);

  React.useEffect(() => {
    if (autoHideDuration > 0) {
      const timer = setTimeout(() => {
        setOpen(false);
        onDismiss?.();
      }, autoHideDuration);
      return () => clearTimeout(timer);
    }
  }, [autoHideDuration, onDismiss]);

  return (
    <Collapse in={open}>
      <Alert 
        severity="success" 
        onClose={() => {
          setOpen(false);
          onDismiss?.();
        }}
        sx={{ mb: 2 }}
      >
        {message}
      </Alert>
    </Collapse>
  );
};