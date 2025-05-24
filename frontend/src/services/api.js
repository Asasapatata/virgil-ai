class CodeGeneratorAPI {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  /**
   * Upload requirements file
   */
  async uploadRequirements(file, customProjectName = null) {
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

  /**
   * Generate project using existing method
   */
  async generateProject(projectId, provider = 'openai', maxIterations = 10) {
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

  async generateProjectSmart(projectId, provider = 'openai', overrideAgentMode = null, overrideMaxIterations = null) {
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
      console.error('Error generating project:', error);
      throw error;
    }
  }

  /**
   * Generate project using multi-agent
   */
  async generateProjectWithAgents(projectId, provider = 'openai', maxIterations = 10) {
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
  async generateEnhancedProject(projectId, provider = 'openai', maxIterations = 10) {
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
  async getProjectStatus(projectId) {
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
  async downloadProject(projectId, iteration = null) {
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
  async downloadFinalProject(projectId) {
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
  async cleanupProject(projectId, keepFinal = true) {
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
   * Stop Generation - CORRETTO: ora è un metodo della classe anziché una proprietà
   */
  async stopGeneration(projectId) {
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
  async canStopGeneration(projectId) {
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
}

// Export
export default CodeGeneratorAPI;