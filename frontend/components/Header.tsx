// components/Header.tsx
import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  IconButton,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Person as PersonIcon,
  Logout as LogoutIcon,
  Info as InfoIcon,
  Brightness4 as ThemeIcon
} from '@mui/icons-material';

interface HeaderProps {
  onSettingsClick?: () => void;
  onProfileClick?: () => void;
}

const Header: React.FC<HeaderProps> = ({ onSettingsClick, onProfileClick }) => {
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  return (
    <AppBar 
      position="sticky" 
      elevation={0}
      sx={{ 
        bgcolor: 'background.paper',
        borderBottom: 1,
        borderColor: 'divider',
        zIndex: (theme) => theme.zIndex.drawer + 1
      }}
    >
      <Toolbar sx={{ minHeight: 64 }}>
        {/* Logo e Titolo */}
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          <Box 
            sx={{ 
              width: 36, 
              height: 36, 
              bgcolor: 'primary.main', 
              borderRadius: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mr: 2
            }}
          >
            <Typography 
              variant="h6" 
              sx={{ 
                color: 'white', 
                fontWeight: 'bold',
                fontSize: '1.2rem'
              }}
            >
              AI
            </Typography>
          </Box>
          <Typography 
            variant="h6" 
            sx={{ 
              color: 'text.primary',
              fontWeight: 600
            }}
          >
            Virgil AI
          </Typography>
        </Box>

        {/* Right side actions */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {/* Settings Button */}
          <IconButton
            onClick={onSettingsClick}
            sx={{ 
              color: 'text.secondary',
              '&:hover': { 
                bgcolor: 'action.hover' 
              }
            }}
          >
            <SettingsIcon />
          </IconButton>

          {/* User Menu */}
          <IconButton
            onClick={handleMenuClick}
            sx={{ p: 0 }}
          >
            <Avatar 
              sx={{ 
                width: 32, 
                height: 32,
                bgcolor: 'primary.main'
              }}
            >
              <PersonIcon sx={{ fontSize: 20 }} />
            </Avatar>
          </IconButton>

          {/* User Menu Dropdown */}
          <Menu
            anchorEl={anchorEl}
            open={open}
            onClose={handleMenuClose}
            onClick={handleMenuClose}
            PaperProps={{
              elevation: 3,
              sx: {
                overflow: 'visible',
                filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
                mt: 1.5,
                minWidth: 200,
                '&:before': {
                  content: '""',
                  display: 'block',
                  position: 'absolute',
                  top: 0,
                  right: 14,
                  width: 10,
                  height: 10,
                  bgcolor: 'background.paper',
                  transform: 'translateY(-50%) rotate(45deg)',
                  zIndex: 0,
                },
              },
            }}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            <MenuItem onClick={onProfileClick}>
              <ListItemIcon>
                <PersonIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Profilo</ListItemText>
            </MenuItem>
            
            <MenuItem>
              <ListItemIcon>
                <ThemeIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Tema</ListItemText>
            </MenuItem>
            
            <Divider />
            
            <MenuItem>
              <ListItemIcon>
                <InfoIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Info & Help</ListItemText>
            </MenuItem>
            
            <MenuItem>
              <ListItemIcon>
                <LogoutIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Logout</ListItemText>
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
