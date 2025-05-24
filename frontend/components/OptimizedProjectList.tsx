import React, { useMemo, useState, useCallback } from 'react';
import {
  Box,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
  CircularProgress,
  Button,
  Skeleton
} from '@mui/material';
import {
  Search as SearchIcon,
  Folder as FolderIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Add as AddIcon,
  CloudUpload as CloudUploadIcon
} from '@mui/icons-material';
import { Project } from '../hooks/useProjectStorage';

interface OptimizedProjectListProps {
  projects: Project[];
  selectedProject: Project | null;
  onSelectProject: (project: Project) => void;
  onCreateProject: () => void;
  onImportProject: () => void;
  loading: boolean;
  polling: Set<string>;
}

const OptimizedProjectList: React.FC<OptimizedProjectListProps> = ({
  projects,
  selectedProject,
  onSelectProject,
  onCreateProject,
  onImportProject,
  loading,
  polling
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'name' | 'date' | 'status'>('date');

  // Memoized filtered and sorted projects
  const filteredProjects = useMemo(() => {
    let filtered = projects;

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(project =>
        project.project_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        project.description?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(project => project.status === statusFilter);
    }

    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.project_name.localeCompare(b.project_name);
        case 'status':
          return a.status.localeCompare(b.status);
        case 'date':
        default:
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }
    });

    return filtered;
  }, [projects, searchTerm, statusFilter, sortBy]);

  const statusCounts = useMemo(() => {
    const counts = projects.reduce((acc, project) => {
      acc[project.status] = (acc[project.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    return counts;
  }, [projects]);

  const getStatusColor = useCallback((status: Project['status']) => {
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
  }, []);

  const getStatusIcon = useCallback((status: Project['status'], isPolling = false) => {
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
  }, []);

  const getStatusLabel = useCallback((status: Project['status']) => {
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
  }, []);

  const formatDate = useCallback((dateString: string) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }, []);

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header con button per nuovo progetto */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
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

        {/* Search */}
        <TextField
          fullWidth
          size="small"
          placeholder="Cerca progetti..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          disabled={loading}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon sx={{ color: 'text.secondary' }} />
              </InputAdornment>
            )
          }}
          sx={{ mb: 1.5 }}
        />

        {/* Filters row */}
        <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Stato</InputLabel>
            <Select
              value={statusFilter}
              label="Stato"
              onChange={(e) => setStatusFilter(e.target.value)}
              disabled={loading}
            >
              <MenuItem value="all">
                Tutti ({projects.length})
              </MenuItem>
              <MenuItem value="completed">
                Completati ({statusCounts.completed || 0})
              </MenuItem>
              <MenuItem value="processing">
                In corso ({(statusCounts.processing || 0) + (statusCounts.generating_code || 0) + (statusCounts.generating_tests || 0) + (statusCounts.running_tests || 0)})
              </MenuItem>
              <MenuItem value="failed">
                Falliti ({(statusCounts.failed || 0) + (statusCounts.error || 0)})
              </MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Ordina per</InputLabel>
            <Select
              value={sortBy}
              label="Ordina per"
              onChange={(e) => setSortBy(e.target.value as any)}
              disabled={loading}
            >
              <MenuItem value="date">Data</MenuItem>
              <MenuItem value="name">Nome</MenuItem>
              <MenuItem value="status">Stato</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {/* Active filters */}
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
          {searchTerm && (
            <Chip
              label={`Ricerca: "${searchTerm}"`}
              size="small"
              onDelete={() => setSearchTerm('')}
            />
          )}
          {statusFilter !== 'all' && (
            <Chip
              label={`Stato: ${statusFilter}`}
              size="small"
              onDelete={() => setStatusFilter('all')}
            />
          )}
        </Box>
      </Box>

      {/* Results info */}
      <Box sx={{ px: 2, py: 1, bgcolor: 'background.default' }}>
        <Typography variant="caption" color="text.secondary">
          {filteredProjects.length} di {projects.length} progetti
          {polling.size > 0 && (
            <Chip
              label={`${polling.size} in monitoraggio`}
              size="small"
              color="warning"
              sx={{ ml: 1 }}
            />
          )}
        </Typography>
      </Box>

      {/* Projects list */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {loading && projects.length === 0 ? (
          <Box sx={{ p: 2 }}>
            {[...Array(5)].map((_, i) => (
              <Box key={i} sx={{ mb: 2 }}>
                <Skeleton variant="rectangular" height={80} sx={{ borderRadius: 1 }} />
              </Box>
            ))}
          </Box>
        ) : filteredProjects.length > 0 ? (
          <List sx={{ p: 1.5, pt: 1 }}>
            {filteredProjects.map((project) => (
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
        ) : (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <FolderIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {loading ? 'Caricamento...' : 
               searchTerm || statusFilter !== 'all'
                ? 'Nessun progetto corrisponde ai filtri'
                : 'Nessun progetto trovato'
              }
            </Typography>
            {!loading && projects.length === 0 && (
              <Typography variant="caption" color="text.secondary">
                Crea il tuo primo progetto per iniziare
              </Typography>
            )}
          </Box>
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
    </Box>
  );
};

export default OptimizedProjectList;