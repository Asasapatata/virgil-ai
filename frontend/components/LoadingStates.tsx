import React from 'react';
import {
  Box,
  Skeleton,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  LinearProgress,
  Fade,
  Grow
} from '@mui/material';

// Enhanced skeleton for project list
export const ProjectListSkeleton: React.FC = () => (
  <Box sx={{ p: 1.5 }}>
    {[...Array(4)].map((_, i) => (
      <Card key={i} sx={{ mb: 1, opacity: 1 - i * 0.1 }}>
        <CardContent sx={{ py: 1.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Skeleton variant="circular" width={36} height={36} />
            <Box sx={{ flex: 1 }}>
              <Skeleton 
                variant="text" 
                width="60%" 
                height={24}
                sx={{ mb: 0.5 }}
              />
              <Skeleton variant="text" width="40%" height={16} />
              <Skeleton variant="text" width="80%" height={14} />
            </Box>
            <Skeleton variant="rounded" width={80} height={22} />
          </Box>
        </CardContent>
      </Card>
    ))}
  </Box>
);

// Animated loading for creation process
export const CreationLoader: React.FC<{ message?: string }> = ({ 
  message = "Creazione in corso..." 
}) => (
  <Fade in timeout={300}>
    <Box 
      sx={{ 
        display: 'flex', 
        flexDirection: 'column',
        alignItems: 'center',
        p: 4,
        textAlign: 'center'
      }}
    >
      <Box sx={{ position: 'relative', mb: 3 }}>
        <CircularProgress
          size={60}
          thickness={4}
          sx={{ 
            color: 'primary.main',
            animationDuration: '2s'
          }}
        />
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            fontSize: '1.5rem'
          }}
        >
          🚀
        </Box>
      </Box>
      <Typography variant="h6" gutterBottom>
        {message}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        Stiamo elaborando la tua richiesta...
      </Typography>
    </Box>
  </Fade>
);

// Progress indicator with steps
export const ProgressSteps: React.FC<{
  currentStep: number;
  steps: string[];
  isComplete?: boolean;
}> = ({ currentStep, steps, isComplete = false }) => (
  <Box sx={{ width: '100%', mt: 2 }}>
    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
      {steps.map((step, index) => (
        <Typography
          key={index}
          variant="caption"
          sx={{
            color: index <= currentStep ? 'primary.main' : 'text.secondary',
            fontWeight: index === currentStep ? 'bold' : 'normal'
          }}
        >
          {index + 1}. {step}
        </Typography>
      ))}
    </Box>
    <LinearProgress
      variant="determinate"
      value={isComplete ? 100 : (currentStep / (steps.length - 1)) * 100}
      sx={{
        height: 8,
        borderRadius: 1,
        '& .MuiLinearProgress-bar': {
          borderRadius: 1,
          transition: 'transform 0.5s ease-in-out'
        }
      }}
    />
  </Box>
);

// Empty state with call to action
export const EmptyState: React.FC<{
  icon: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
}> = ({ icon, title, description, action }) => (
  <Grow in timeout={500}>
    <Box 
      sx={{ 
        textAlign: 'center',
        p: 4,
        maxWidth: 400,
        mx: 'auto'
      }}
    >
      <Box sx={{ fontSize: '4rem', mb: 2, opacity: 0.6 }}>
        {icon}
      </Box>
      <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {description}
      </Typography>
      {action && action}
    </Box>
  </Grow>
);

// Pulse effect for active states
export const PulseBox: React.FC<{
  children: React.ReactNode;
  isActive?: boolean;
}> = ({ children, isActive = false }) => (
  <Box
    sx={{
      animation: isActive ? 'pulse 2s infinite' : 'none',
      '@keyframes pulse': {
        '0%': {
          boxShadow: '0 0 0 0 rgba(25, 118, 210, 0.4)'
        },
        '70%': {
          boxShadow: '0 0 0 10px rgba(25, 118, 210, 0)'
        },
        '100%': {
          boxShadow: '0 0 0 0 rgba(25, 118, 210, 0)'
        }
      }
    }}
  >
    {children}
  </Box>
);

// Smooth slide transition
export const SlideTransition: React.FC<{
  children: React.ReactNode;
  direction?: 'left' | 'right' | 'up' | 'down';
  duration?: number;
}> = ({ children, direction = 'up', duration = 300 }) => {
  const getTransform = () => {
    switch (direction) {
      case 'left': return 'translateX(-20px)';
      case 'right': return 'translateX(20px)';
      case 'up': return 'translateY(20px)';
      case 'down': return 'translateY(-20px)';
      default: return 'translateY(20px)';
    }
  };

  return (
    <Box
      sx={{
        animation: `slideIn ${duration}ms ease-out`,
        '@keyframes slideIn': {
          from: {
            opacity: 0,
            transform: getTransform()
          },
          to: {
            opacity: 1,
            transform: 'translate(0)'
          }
        }
      }}
    >
      {children}
    </Box>
  );
};