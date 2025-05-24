// components/ResponsiveLayout.tsx - Layout responsive per mobile
import React, { useState, useEffect } from 'react';
import {
  Box,
  Drawer,
  useMediaQuery,
  useTheme,
  IconButton,
  AppBar,
  Toolbar,
  Typography,
  SwipeableDrawer,
  Fab,
  Backdrop
} from '@mui/material';
import {
  Menu as MenuIcon,
  Add as AddIcon,
  Close as CloseIcon
} from '@mui/icons-material';

interface ResponsiveLayoutProps {
  sidebar: React.ReactNode;
  main: React.ReactNode;
  header?: React.ReactNode;
  onCreateProject?: () => void;
}

const ResponsiveLayout: React.FC<ResponsiveLayoutProps> = ({
  sidebar,
  main,
  header,
  onCreateProject
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isTablet = useMediaQuery(theme.breakpoints.down('lg'));
  
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const [touchStartX, setTouchStartX] = useState(0);

  // Close drawer on route change (mobile)
  useEffect(() => {
    if (isMobile) {
      setMobileDrawerOpen(false);
    }
  }, [isMobile]);

  // Swipe gesture handling
  const handleTouchStart = (event: React.TouchEvent) => {
    setTouchStartX(event.touches[0].clientX);
  };

  const handleTouchEnd = (event: React.TouchEvent) => {
    const touchEndX = event.changedTouches[0].clientX;
    const swipeDistance = touchEndX - touchStartX;
    
    // Swipe right to open (from left edge)
    if (swipeDistance > 50 && touchStartX < 50 && isMobile) {
      setMobileDrawerOpen(true);
    }
    // Swipe left to close
    else if (swipeDistance < -50 && mobileDrawerOpen) {
      setMobileDrawerOpen(false);
    }
  };

  const drawerWidth = isMobile ? '85vw' : isTablet ? 300 : 340;

  const drawer = (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'background.paper'
      }}
    >
      {/* Mobile header */}
      {isMobile && (
        <Box sx={{ 
          p: 2, 
          borderBottom: 1, 
          borderColor: 'divider',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <Typography variant="h6">AI Code Generator</Typography>
          <IconButton onClick={() => setMobileDrawerOpen(false)}>
            <CloseIcon />
          </IconButton>
        </Box>
      )}
      
      {/* Sidebar content */}
      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        {sidebar}
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* Header for mobile */}
      {isMobile && (
        <AppBar 
          position="fixed" 
          sx={{ 
            zIndex: theme.zIndex.drawer + 1,
            bgcolor: 'background.paper',
            color: 'text.primary',
            boxShadow: 1
          }}
        >
          <Toolbar>
            <IconButton
              edge="start"
              onClick={() => setMobileDrawerOpen(true)}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
              AI Code Generator
            </Typography>
          </Toolbar>
        </AppBar>
      )}

      {/* Desktop header */}
      {!isMobile && header && (
        <Box sx={{ 
          position: 'fixed', 
          top: 0, 
          left: 0, 
          right: 0, 
          zIndex: theme.zIndex.appBar 
        }}>
          {header}
        </Box>
      )}

      {/* Sidebar */}
      {isMobile ? (
        <SwipeableDrawer
          anchor="left"
          open={mobileDrawerOpen}
          onClose={() => setMobileDrawerOpen(false)}
          onOpen={() => setMobileDrawerOpen(true)}
          ModalProps={{
            keepMounted: true, // Better mobile performance
          }}
          PaperProps={{
            sx: { 
              width: drawerWidth,
              maxWidth: '85vw'
            }
          }}
        >
          {drawer}
        </SwipeableDrawer>
      ) : (
        <Drawer
          variant="permanent"
          sx={{
            width: drawerWidth,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: drawerWidth,
              boxSizing: 'border-box',
              position: 'relative',
              height: '100vh'
            },
          }}
        >
          {drawer}
        </Drawer>
      )}

      {/* Main content */}
      <Box
        component="main"
        sx={{
          flex: 1,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          mt: isMobile ? 8 : header ? 8 : 0, // Account for fixed header
          height: isMobile ? 'calc(100vh - 64px)' : '100vh'
        }}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        {main}
      </Box>

      {/* Mobile FAB for new project */}
      {isMobile && onCreateProject && (
        <Fab
          color="primary"
          aria-label="add project"
          onClick={onCreateProject}
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            zIndex: theme.zIndex.fab
          }}
        >
          <AddIcon />
        </Fab>
      )}

      {/* Backdrop for mobile drawer */}
      {isMobile && mobileDrawerOpen && (
        <Backdrop
          open={mobileDrawerOpen}
          onClick={() => setMobileDrawerOpen(false)}
          sx={{ zIndex: theme.zIndex.drawer - 1 }}
        />
      )}
    </Box>
  );
};

export default ResponsiveLayout;