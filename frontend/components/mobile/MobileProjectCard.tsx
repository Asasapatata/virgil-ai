import React from 'react';
import {
  Card,
  CardContent,
  Box,
  Typography,
  Chip,
  IconButton,
  Avatar,
  Slide,
  useTheme,
  alpha
} from '@mui/material';
import {
  MoreVert as MoreVertIcon,
  CloudDownload as DownloadIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { Project } from '../../hooks/useProjectStorage';

interface MobileProjectCardProps {
  project: Project;
  isSelected: boolean;
  onSelect: () => void;
  onDownload?: () => void;
  onRegenerate?: () => void;
  onMore?: () => void;
  isPolling?: boolean;
  index: number;
}

const MobileProjectCard: React.FC<MobileProjectCardProps> = ({
  project,
  isSelected,
  onSelect,
  onDownload,
  onRegenerate,
  onMore,
  isPolling,
  index
}) => {
  const theme = useTheme();

  const getStatusColor = (status: Project['status']) => {
    switch (status) {
      case 'completed': return theme.palette.success.main;
      case 'processing':
      case 'generating_code':
      case 'generating_tests':
      case 'running_tests': return theme.palette.warning.main;
      case 'failed':
      case 'error': return theme.palette.error.main;
      default: return theme.palette.grey[500];
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 1) return 'Oggi';
    if (diffDays === 2) return 'Ieri';
    if (diffDays <= 7) return `${diffDays} giorni fa`;
    return date.toLocaleDateString('it-IT');
  };

  return (
    <Slide direction="up" in timeout={300 + index * 100}>
      <Card
        onClick={onSelect}
        sx={{
          mb: 2,
          mx: 1,
          transition: 'all 0.3s ease',
          transform: isSelected ? 'scale(1.02)' : 'scale(1)',
          boxShadow: isSelected ? 4 : 1,
          borderLeft: 4,
          borderLeftColor: getStatusColor(project.status),
          bgcolor: isSelected 
            ? alpha(theme.palette.primary.main, 0.05)
            : 'background.paper',
          '&:active': {
            transform: 'scale(0.98)',
          },
          cursor: 'pointer'
        }}
      >
        <CardContent sx={{ p: 2 }}>
          {/* Header with title and actions */}
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            mb: 1.5
          }}>
            <Box sx={{ flex: 1, pr: 1 }}>
              <Typography 
                variant="h6" 
                sx={{ 
                  fontSize: '1.1rem',
                  fontWeight: 600,
                  lineHeight: 1.2,
                  color: isSelected ? 'primary.main' : 'text.primary'
                }}
                noWrap
              >
                {project.project_name}
              </Typography>
              {project.description && (
                <Typography 
                  variant="body2" 
                  color="text.secondary"
                  sx={{ 
                    mt: 0.5,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical'
                  }}
                >
                  {project.description}
                </Typography>
              )}
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              {/* Quick actions for completed projects */}
              {project.status === 'completed' && (
                <>
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDownload?.();
                    }}
                    sx={{ p: 0.5 }}
                  >
                    <DownloadIcon fontSize="small" />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      onRegenerate?.();
                    }}
                    sx={{ p: 0.5 }}
                  >
                    <RefreshIcon fontSize="small" />
                  </IconButton>
                </>
              )}
              
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  onMore?.();
                }}
                sx={{ p: 0.5 }}
              >
                <MoreVertIcon fontSize="small" />
              </IconButton>
            </Box>
          </Box>

          {/* Status and metadata */}
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 1
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Avatar 
                sx={{ 
                  width: 20, 
                  height: 20,
                  bgcolor: getStatusColor(project.status)
                }}
              >
                {isPolling ? '⏳' : 
                 project.status === 'completed' ? '✓' :
                 project.status === 'failed' ? '✗' : '◐'}
              </Avatar>
              
              <Chip
                label={project.status}
                size="small"
                sx={{
                  height: 24,
                  fontSize: '0.75rem',
                  bgcolor: alpha(getStatusColor(project.status), 0.1),
                  color: getStatusColor(project.status),
                  border: `1px solid ${alpha(getStatusColor(project.status), 0.3)}`
                }}
              />

              {project.current_iteration !== undefined && (
                <Chip
                  label={`${project.current_iteration}/10`}
                  size="small"
                  variant="outlined"
                  sx={{ height: 24, fontSize: '0.75rem' }}
                />
              )}
            </Box>

            <Typography 
              variant="caption" 
              color="text.secondary"
              sx={{ fontSize: '0.75rem' }}
            >
              {formatDate(project.created_at)}
            </Typography>
          </Box>

          {/* Progress bar for active projects */}
          {(project.status === 'processing' || 
            project.status === 'generating_code' || 
            project.status === 'generating_tests' ||
            project.status === 'running_tests') && 
            project.current_iteration !== undefined && (
            <Box sx={{ mt: 1.5 }}>
              <Box sx={{ 
                height: 4, 
                bgcolor: 'background.default',
                borderRadius: 1,
                overflow: 'hidden'
              }}>
                <Box
                  sx={{
                    height: '100%',
                    bgcolor: getStatusColor(project.status),
                    width: `${(project.current_iteration / 10) * 100}%`,
                    transition: 'width 0.5s ease',
                    borderRadius: 1
                  }}
                />
              </Box>
              <Typography 
                variant="caption" 
                color="text.secondary"
                sx={{ fontSize: '0.7rem', mt: 0.5, display: 'block' }}
              >
                Iterazione {project.current_iteration} di 10
              </Typography>
            </Box>
          )}

          {/* Live indicator */}
          {isPolling && (
            <Box sx={{ 
              position: 'absolute',
              top: 8,
              right: 8,
              width: 8,
              height: 8,
              borderRadius: '50%',
              bgcolor: 'warning.main',
              animation: 'pulse 2s infinite',
              '@keyframes pulse': {
                '0%': {
                  boxShadow: '0 0 0 0 rgba(255, 152, 0, 0.7)'
                },
                '70%': {
                  boxShadow: '0 0 0 6px rgba(255, 152, 0, 0)'
                },
                '100%': {
                  boxShadow: '0 0 0 0 rgba(255, 152, 0, 0)'
                }
              }
            }} />
          )}
        </CardContent>
      </Card>
    </Slide>
  );
};

export default MobileProjectCard;