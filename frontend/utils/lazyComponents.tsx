import React, { lazy, Suspense } from 'react';
import { CircularProgress, Box } from '@mui/material';

// Lazy load components esistenti (aggiusta i path in base alla tua struttura)
export const LazyProjectDetails = lazy(() => import('../components/ProjectDetails'));
export const LazyCreateProjectDialog = lazy(() => import('../components/CreateProjectDialog'));
export const LazyOptimizedProjectList = lazy(() => import('../components/OptimizedProjectList'));

// Loading fallback component
const LoadingFallback: React.FC = () => (
  <Box 
    sx={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      height: 200 
    }}
  >
    <CircularProgress />
  </Box>
);

// HOC per wrappare componenti lazy con Suspense
export const withSuspense = <P extends Record<string, any>>(
  Component: React.ComponentType<P>,
  Fallback: React.ComponentType = LoadingFallback
) => {
  const SuspenseComponent: React.FC<P> = (props) => (
    <Suspense fallback={<Fallback />}>
      <Component {...props} />
    </Suspense>
  );
  
  SuspenseComponent.displayName = `withSuspense(${Component.displayName || Component.name})`;
  return SuspenseComponent;
};

// Performance utilities
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  delay: number
): ((...args: Parameters<T>) => void) => {
  let timeoutId: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
};

export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  delay: number
): ((...args: Parameters<T>) => void) => {
  let timeoutId: NodeJS.Timeout | null = null;
  let lastExecTime = 0;
  
  return (...args: Parameters<T>) => {
    const currentTime = Date.now();
    
    if (currentTime - lastExecTime > delay) {
      func(...args);
      lastExecTime = currentTime;
    } else {
      if (timeoutId) clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        func(...args);
        lastExecTime = Date.now();
      }, delay - (currentTime - lastExecTime));
    }
  };
};

// Memory management utilities
export const useMemoryOptimization = () => {
  // Clear unused data from localStorage if it gets too big
  const cleanupLocalStorage = (): void => {
    try {
      const totalSize = Object.keys(localStorage).reduce((total, key) => {
        return total + (localStorage.getItem(key)?.length || 0);
      }, 0);
      
      // If localStorage is > 4MB, cleanup old projects
      if (totalSize > 4 * 1024 * 1024) {
        const projects = JSON.parse(localStorage.getItem('ai_code_generator_projects') || '[]');
        // Keep only last 50 projects
        const trimmed = projects.slice(0, 50);
        localStorage.setItem('ai_code_generator_projects', JSON.stringify(trimmed));
      }
    } catch (error) {
      console.warn('Failed to cleanup localStorage:', error);
    }
  };

  // Image optimization for screenshots/previews
  const optimizeImage = (file: File, maxWidth = 800, quality = 0.8): Promise<Blob> => {
    return new Promise((resolve, reject) => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      if (!ctx) {
        reject(new Error('Failed to get canvas context'));
        return;
      }
      
      const img = new Image();
      
      img.onload = () => {
        const ratio = Math.min(maxWidth / img.width, maxWidth / img.height);
        canvas.width = img.width * ratio;
        canvas.height = img.height * ratio;
        
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        
        canvas.toBlob((blob) => {
          if (blob) {
            resolve(blob);
          } else {
            reject(new Error('Failed to create blob'));
          }
        }, 'image/jpeg', quality);
      };
      
      img.onerror = () => reject(new Error('Failed to load image'));
      img.src = URL.createObjectURL(file);
    });
  };

  // Memoize expensive calculations
  const memoize = <T extends (...args: any[]) => any>(fn: T) => {
    const cache = new Map<string, ReturnType<T>>();
    
    return ((...args: Parameters<T>): ReturnType<T> => {
      const key = JSON.stringify(args);
      
      if (cache.has(key)) {
        const cachedResult = cache.get(key);
        if (cachedResult !== undefined) {
          return cachedResult;
        }
      }
      
      const result = fn(...args);
      cache.set(key, result);
      
      // Limit cache size to prevent memory leaks
      if (cache.size > 100) {
        const firstKey = cache.keys().next().value;
        if (firstKey !== undefined) {
          cache.delete(firstKey);
        }
      }
      
      return result;
    }) as T;
  };

  return {
    cleanupLocalStorage,
    optimizeImage,
    memoize
  };
};