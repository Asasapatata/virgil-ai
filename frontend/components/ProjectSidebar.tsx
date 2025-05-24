// components/ProjectSidebar.tsx
import React from 'react';
import {
  Paper,
  Box,
  Typography,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
  Chip,
  CircularProgress,
  Skeleton
} from '@mui/material';
import {
  Add as AddIcon,
  Folder as FolderIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  CloudUpload as CloudUploadIcon
} from '@mui/icons-material';
import { Project } from '../hooks/useProjectStorage';

interface ProjectSidebarProps {
  projects: Project[];
  selectedProject: Project | null;
  onSelectProject: (project: Project) => void;
  onCreateProject: () => void;
  onImportProject: () => void;
  loading: boolean;
  polling: Set<string>;
}

const ProjectSidebar: React.FC<ProjectSidebarProps> = ({
  projects,
  selectedProject,
  onSelectProject,
  onCreateProject,
  onImportProject,
  loading,
  polling
}) => {
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

  const getStatusIcon = (status: Project['status'], isPolling = false) => {
    switch (status) {
      case 'completed': return <CheckCircleIcon />;
      case 'processing':
      case 'generating_code':
      case 'generating_tests':
      case 'running_tests':
        return isPolling ? <CircularProgress size={20} /> : <ScheduleIcon />;
      case 'failed':
      case 'error': return <ErrorIcon />;
      default: return <FolderIcon />;
    }
  };

  const getStatusLabel = (status: Project['status']) => {
    switch (status) {
      case 'uploaded': return 'Caricato';
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

  return (
    <Paper 
      elevation={1} 
      sx={{ 
        width: 340, 
        display: 'flex', 
        flexDirection: 'column',
        borderRadius: 2,
        height: '100%'
      }}
    >
      {/* Header */}
      <Box sx={{ p: 2.5, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6" component="h2" sx={{ fontWeight: 600 }}>
            Progetti ({projects.length})
          </Typography>
          <Button
            variant="contained"
            size="small"
            startIcon={<AddIcon />}
            onClick={onCreateProject}
            disabled={loading}
            sx={{ borderRadius: 2 }}
          >
            Nuovo
          </Button>
          <Button
              variant="outlined"
              size="small"
              startIcon={<CloudUploadIcon />}
              onClick={onImportProject}
              disabled={loading}
              sx={{ borderRadius: 2 }}
            >
              Importa
            </Button>
        </Box>
      </Box>
      

      {/* Projects List */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {loading && projects.length === 0 ? (
          <Box sx={{ p: 2 }}>
            {[...Array(3)].map((_, i) => (
              <Box key={i} sx={{ mb: 2 }}>
                <Skeleton variant="rectangular" height={80} sx={{ borderRadius: 1 }} />
              </Box>
            ))}
          </Box>
        ) : projects.length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <FolderIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Nessun progetto
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Crea il tuo primo progetto per iniziare
            </Typography>
          </Box>
        ) : (
          <List sx={{ p: 1.5, pt: 1 }}>
            {projects.map((project) => (
              <ListItem
                key={project.project_id}
                button
                selected={selectedProject?.project_id === project.project_id}
                onClick={() => onSelectProject(project)}
                sx={{ 
                  mb: 1, 
                  borderRadius: 2,
                  border: 1,
                  borderColor: selectedProject?.project_id === project.project_id 
                    ? 'primary.main' 
                    : 'transparent',
                  '&.Mui-selected': {
                    bgcolor: 'primary.lighter',
                    '&:hover': {
                      bgcolor: 'primary.lighter'
                    }
                  },
                  '&:hover': {
                    bgcolor: 'action.hover',
                    borderColor: 'divider'
                  }
                }}
              >
                <ListItemIcon>
                  <Avatar sx={{ width: 36, height: 36 }}>
                    {getStatusIcon(project.status, polling.has(project.project_id))}
                  </Avatar>
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                      <Typography variant="subtitle2" noWrap sx={{ fontWeight: 500 }}>
                        {project.project_name}
                      </Typography>
                      <Chip 
                        label={getStatusLabel(project.status)} 
                        size="small" 
                        color={getStatusColor(project.status)}
                        variant="outlined"
                        sx={{ fontSize: '0.75rem', height: 22 }}
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      {project.description && (
                        <Typography variant="caption" display="block" noWrap sx={{ color: 'text.secondary' }}>
                          {project.description}
                        </Typography>
                      )}
                      <Typography variant="caption" color="text.secondary">
                        {formatDate(project.created_at)}
                      </Typography>
                      {project.current_iteration !== undefined && (
                        <Typography variant="caption" display="block" color="primary.main" sx={{ fontWeight: 500 }}>
                          Iterazione {project.current_iteration}/10
                        </Typography>
                      )}
                      {polling.has(project.project_id) && (
                        <Typography variant="caption" display="block" sx={{ color: 'warning.main', fontWeight: 500 }}>
                          • Live
                        </Typography>
                      )}
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </Box>

      {/* Footer */}
      <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', bgcolor: 'background.default' }}>
        <Typography variant="caption" color="text.secondary">
          Virgil AI v1.0
        </Typography>
        {polling.size > 0 && (
          <Typography variant="caption" display="block" sx={{ color: 'warning.main', fontWeight: 500 }}>
            {polling.size} progetto{polling.size > 1 ? 'i' : ''} in monitoraggio
          </Typography>
        )}
      </Box>
    </Paper>
  );
};

export default ProjectSidebar;
