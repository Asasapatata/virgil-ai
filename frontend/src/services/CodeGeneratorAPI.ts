// Versione corretta di CodeGeneratorAPI.ts

/**
 * TypeScript wrapper per CodeGeneratorAPI
 */
class CodeGeneratorAPI {
  baseUrl: string;
  

  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  /**
   * Upload requirements file
   */
  async uploadRequirements(file: File, customProjectName: string | null = null) {
    const formData = new FormData();
    formData.append('file', file);

    // Aggiungi il nome del progetto personalizzato se fornito
    if (customProjectName && customProjectName.trim()) {
      formData.append('project_name', customProjectName.trim());
      console.log(`Sending custom project name to backend: ${customProjectName.trim()}`);
    }

    try {
      const response = await fetch(`${this.baseUrl}/upload-requirements`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error uploading requirements:', error);
      throw error;
    }
  }

  async analyzeRequirements(projectId: string) {
    try {
      const response = await fetch(`${this.baseUrl}/api/analyze-requirements/${projectId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error analyzing requirements:', error);
      throw error;
    }
  }

  /**
   * Ottieni breakdown dettagliato della complessità
   */
  async getComplexityBreakdown(projectId: string) {
    try {
      const response = await fetch(`${this.baseUrl}/api/complexity-analysis/${projectId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting complexity breakdown:', error);
      throw error;
    }
  }

  /**
   * Ottieni informazioni sui modi agente disponibili
   */
  async getAgentModes() {
    try {
      const response = await fetch(`${this.baseUrl}/api/agent-modes`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting agent modes:', error);
      throw error;
    }
  }

  /**
   * Genera progetto usando il router intelligente
   */
  async generateProjectSmart(projectId: string, provider = 'anthropic', overrideAgentMode = null, overrideMaxIterations = null) {
    try {
      const response = await fetch(`${this.baseUrl}/api/smart-generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_id: projectId,
          llm_provider: provider,
          override_agent_mode: overrideAgentMode,
          override_max_iterations: overrideMaxIterations
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error generating project with smart router:', error);
      throw error;
    }
  }

  /**
   * Generate project using existing method
   */
  async generateProject(projectId: string, provider = 'openai', maxIterations = 10) {
    try {
      const response = await fetch(`${this.baseUrl}/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_id: projectId,
          llm_provider: provider,
          max_iterations: maxIterations
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error generating project:', error);
      throw error;
    }
  }

  /**
   * Generate project using multi-agent
   */
  async generateProjectWithAgents(projectId: string, provider = 'openai', maxIterations = 10) {
    try {
      const response = await fetch(`${this.baseUrl}/generate-with-agents`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_id: projectId,
          llm_provider: provider,
          max_iterations: maxIterations
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error generating project:', error);
      throw error;
    }
  }

  /**
   * Generate project using enhanced method
   */
  async generateEnhancedProject(projectId: string, provider = 'openai', maxIterations = 10) {
    try {
      const response = await fetch(`${this.baseUrl}/generate-enhanced`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_id: projectId,
          llm_provider: provider,
          max_iterations: maxIterations,
          use_enhanced: true
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error generating enhanced project:', error);
      throw error;
    }
  }

  /**
   * Get project status
   */
  async getProjectStatus(projectId: string) {
    try {
      const response = await fetch(`${this.baseUrl}/project/${projectId}/status`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting project status:', error);
      throw error;
    }
  }

  /**
   * Download project iteration
   */
  async downloadProject(projectId: string, iteration: number | null = null) {
    try {
      const url = iteration 
        ? `${this.baseUrl}/project/${projectId}/download?iteration=${iteration}`
        : `${this.baseUrl}/project/${projectId}/download`;
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Trigger download
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `${projectId}${iteration ? `_iter_${iteration}` : ''}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(downloadUrl);
      document.body.removeChild(a);

      return true;
    } catch (error) {
      console.error('Error downloading project:', error);
      throw error;
    }
  }

  /**
   * Download final project
   */
  async downloadFinalProject(projectId: string) {
    try {
      const response = await fetch(`${this.baseUrl}/project/${projectId}/download-final`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Trigger download
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `${projectId}_final.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(downloadUrl);
      document.body.removeChild(a);

      return true;
    } catch (error) {
      console.error('Error downloading final project:', error);
      throw error;
    }
  }

  /**
   * Clean up project iterations
   */
  async cleanupProject(projectId: string, keepFinal = true) {
    try {
      const response = await fetch(`${this.baseUrl}/project/${projectId}/cleanup?keep_final=${keepFinal}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error cleaning up project:', error);
      throw error;
    }
  }

  /**
   * Get available LLM providers
   */
  async getLLMProviders() {
    try {
      const response = await fetch(`${this.baseUrl}/llm-providers`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting LLM providers:', error);
      throw error;
    }
  }

  /**
   * Stop Generation - CORRETTO: ora è un metodo della classe
   */
  async stopGeneration(projectId: string) {
    try {
      const response = await fetch(`${this.baseUrl}/project/${projectId}/stop`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error stopping generation:', error);
      throw error;
    }
  }

  /**
   * Check if can stop
   */
  async canStopGeneration(projectId: string) {
    try {
      const response = await fetch(`${this.baseUrl}/project/${projectId}/can-stop`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error checking stop capability:', error);
      throw error;
    }
  }

  // NUOVI METODI: IMPORT PROJECT

  /**
   * Importa un progetto da un file
   */
  async importProjectFromFile(file: File, options?: {
    name?: string;
    description?: string;
    overwrite?: boolean;
  }) {
    const formData = new FormData();
    formData.append('file', file);
    
    if (options?.name) formData.append('name', options.name);
    if (options?.description) formData.append('description', options.description);
    if (options?.overwrite !== undefined) formData.append('overwrite', String(options.overwrite));
    
    try {
      const response = await fetch(`${this.baseUrl}/import-project`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `Import failed: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error importing project from file:', error);
      throw error;
    }
  }

  /**
   * Importa un progetto da GitHub
   */
  async importProjectFromGithub(options: {
    repo_url: string;
    branch?: string;
    name?: string;
    description?: string;
    access_token?: string;
  }) {
    try {
      const response = await fetch(`${this.baseUrl}/import-project-github`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(options),
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `GitHub import failed: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error importing project from GitHub:', error);
      throw error;
    }
  }

  /**
   * Analizza un progetto importato
   */
  async analyzeImportedProject(projectId: string) {
    try {
      const response = await fetch(`${this.baseUrl}/project/${projectId}/analyze`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error analyzing project:', error);
      throw error;
    }
  }

  // NUOVI METODI: MODIFY PROJECT

  /**
   * Modifica un progetto con nuovi requisiti
   */
  async modifyProjectWithRequirements(
    projectId: string, 
    requirementsFile: File,
    options?: {
      mode?: 'incremental' | 'complete_rewrite';
      preserve_existing?: boolean;
      llm_provider?: string;
      max_iterations?: number;
    }
  ) {
    const formData = new FormData();
    formData.append('requirements', requirementsFile);
    formData.append('mode', options?.mode || 'incremental');
    formData.append('preserve_existing', String(options?.preserve_existing ?? true));
    formData.append('llm_provider', options?.llm_provider || 'openai');
    formData.append('max_iterations', String(options?.max_iterations || 5));
    
    try {
      const response = await fetch(`${this.baseUrl}/project/${projectId}/modify`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `Modification failed: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error modifying project:', error);
      throw error;
    }
  }

  /**
   * Anteprima delle modifiche a un progetto
   */
  async previewModifications(
    projectId: string, 
    requirementsFile: File
  ) {
    const formData = new FormData();
    formData.append('requirements', requirementsFile);
    
    try {
      const response = await fetch(`${this.baseUrl}/project/${projectId}/preview-modifications`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`Preview failed: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error previewing modifications:', error);
      throw error;
    }
  }
}

export default CodeGeneratorAPI;