import React, { useState } from 'react';
import CodeGeneratorAPI from '../services/api';

const ProjectGenerator = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [projectData, setProjectData] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState('');
  const [generationResult, setGenerationResult] = useState(null);
  const [useEnhanced, setUseEnhanced] = useState(true);  // Toggle per il metodo
  
  const api = new CodeGeneratorAPI();

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && (file.name.endsWith('.yaml') || file.name.endsWith('.yml'))) {
      setSelectedFile(file);
    } else {
      alert('Please select a YAML file');
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    
    setIsUploading(true);
    setProgress('Uploading requirements...');
    
    try {
      const result = await api.uploadRequirements(selectedFile);
      setProjectData(result);
      setProgress('✅ Requirements uploaded successfully!');
    } catch (error) {
      setProgress(`❌ Upload failed: ${error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleGenerate = async () => {
    if (!projectData?.project_id) return;
    
    setIsGenerating(true);
    setProgress(`Starting ${useEnhanced ? 'enhanced' : 'standard'} generation...`);
    
    try {
      let result;
      
      if (useEnhanced) {
        // Usa il metodo enhanced con merge automatico
        result = await api.generateEnhancedProject(
          projectData.project_id,
          'openai',  // o il provider selezionato
          5          // max iterations
        );
        setGenerationResult(result);
        setProgress(`✅ Enhanced generation completed! ${result.iterations_completed} iterations`);
      } else {
        // Usa il metodo standard (async con Celery)
        result = await api.generateProject(
          projectData.project_id,
          'openai',
          10
        );
        setProgress('🔄 Standard generation started (async)...');
        
        // Polling per controllare lo status
        pollProjectStatus(projectData.project_id);
      }
      
    } catch (error) {
      setProgress(`❌ Generation failed: ${error.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const pollProjectStatus = async (projectId) => {
    const checkStatus = async () => {
      try {
        const status = await api.getProjectStatus(projectId);
        
        if (status.status === 'completed') {
          setGenerationResult({
            project_id: projectId,
            status: 'completed',
            iterations_completed: status.current_iteration,
            has_final: status.has_final
          });
          setProgress('✅ Standard generation completed!');
          return;
        } else if (status.status === 'error') {
          setProgress(`❌ Generation failed: ${status.error || 'Unknown error'}`);
          return;
        }
        
        // Continue polling se ancora in processing
        if (status.status === 'processing') {
          setProgress(`🔄 Processing... (iteration ${status.current_iteration})`);
          setTimeout(checkStatus, 2000);  // Check ogni 2 secondi
        }
      } catch (error) {
        console.error('Error polling status:', error);
        setProgress(`❌ Status check failed: ${error.message}`);
      }
    };
    
    checkStatus();
  };

  const handleDownload = async (final = false) => {
    if (!generationResult?.project_id) return;
    
    try {
      if (final && generationResult.has_final !== false) {
        await api.downloadFinalProject(generationResult.project_id);
      } else {
        await api.downloadProject(generationResult.project_id);
      }
    } catch (error) {
      alert(`Download failed: ${error.message}`);
    }
  };

  const handleCleanup = async () => {
    if (!generationResult?.project_id) return;
    
    try {
      await api.cleanupProject(generationResult.project_id, true);
      alert('Project cleaned up successfully');
    } catch (error) {
      alert(`Cleanup failed: ${error.message}`);
    }
  };

  return (
    <div className="project-generator" style={{padding: '20px', maxWidth: '800px', margin: '0 auto'}}>
      <h1>Virgil AI</h1>
      
      {/* File Upload Section */}
      <div className="upload-section" style={{marginBottom: '30px', padding: '20px', border: '1px solid #ddd', borderRadius: '8px'}}>
        <h2>1. Upload Requirements</h2>
        <input 
          type="file" 
          accept=".yaml,.yml" 
          onChange={handleFileSelect}
          style={{marginBottom: '15px'}}
        />
        {selectedFile && (
          <div>
            <p>Selected: {selectedFile.name}</p>
            <button 
              onClick={handleUpload} 
              disabled={isUploading}
              style={{padding: '10px 20px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px'}}
            >
              {isUploading ? 'Uploading...' : 'Upload Requirements'}
            </button>
          </div>
        )}
      </div>

      {/* Generation Section */}
      {projectData && (
        <div className="generation-section" style={{marginBottom: '30px', padding: '20px', border: '1px solid #ddd', borderRadius: '8px'}}>
          <h2>2. Generate Project</h2>
          <p><strong>Project:</strong> {projectData.project_name}</p>
          <p><strong>ID:</strong> {projectData.project_id}</p>
          
          {/* Method Selection */}
          <div style={{marginBottom: '15px'}}>
            <label style={{display: 'flex', alignItems: 'center', marginBottom: '10px'}}>
              <input 
                type="radio" 
                checked={useEnhanced} 
                onChange={() => setUseEnhanced(true)}
                style={{marginRight: '8px'}}
              />
              Enhanced Mode (Automatic iterations + final merge)
            </label>
            <label style={{display: 'flex', alignItems: 'center'}}>
              <input 
                type="radio" 
                checked={!useEnhanced} 
                onChange={() => setUseEnhanced(false)}
                style={{marginRight: '8px'}}
              />
              Standard Mode (Async with Celery)
            </label>
          </div>
          
          <button 
            onClick={handleGenerate} 
            disabled={isGenerating}
            style={{padding: '10px 20px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px'}}
          >
            {isGenerating ? 'Generating...' : `Generate Project (${useEnhanced ? 'Enhanced' : 'Standard'})`}
          </button>
        </div>
      )}

      {/* Progress Section */}
      {progress && (
        <div className="progress-section" style={{marginBottom: '30px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px'}}>
          <h3>Status</h3>
          <p>{progress}</p>
        </div>
      )}

      {/* Results Section */}
      {generationResult && (
        <div className="results-section" style={{padding: '20px', border: '1px solid #ddd', borderRadius: '8px', backgroundColor: '#f8fff8'}}>
          <h2>3. Download Results</h2>
          <div style={{marginBottom: '15px'}}>
            <p><strong>Project ID:</strong> {generationResult.project_id}</p>
            <p><strong>Status:</strong> {generationResult.status}</p>
            {generationResult.iterations_completed && (
              <p><strong>Iterations Completed:</strong> {generationResult.iterations_completed}</p>
            )}
            {generationResult.file_count && (
              <p><strong>Files Generated:</strong> {generationResult.file_count}</p>
            )}
          </div>
          
          <div className="download-buttons" style={{display: 'flex', gap: '10px', flexWrap: 'wrap'}}>
            {/* Download Final Project (Enhanced mode only) */}
            {useEnhanced && generationResult.has_final !== false && (
              <button 
                onClick={() => handleDownload(true)}
                style={{padding: '10px 20px', backgroundColor: '#17a2b8', color: 'white', border: 'none', borderRadius: '4px'}}
              >
                📦 Download Final Project
              </button>
            )}
            
            {/* Download Latest Iteration */}
            <button 
              onClick={() => handleDownload(false)}
              style={{padding: '10px 20px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '4px'}}
            >
              📄 Download Latest Iteration
            </button>
            
            {/* Cleanup Button */}
            <button 
              onClick={handleCleanup}
              style={{padding: '10px 20px', backgroundColor: '#ffc107', color: 'dark', border: 'none', borderRadius: '4px'}}
            >
              🧹 Cleanup Iterations
            </button>
          </div>
          
          {/* Additional Info for Enhanced Mode */}
          {useEnhanced && (
            <div style={{marginTop: '15px', padding: '10px', backgroundColor: '#e7f3ff', borderRadius: '5px'}}>
              <h4>Enhanced Mode Benefits:</h4>
              <ul style={{margin: '5px 0', paddingLeft: '20px'}}>
                <li>✅ Automatic iterative improvements</li>
                <li>✅ Final project with all files combined</li>
                <li>✅ Ready-to-use download</li>
                <li>✅ Efficient processing</li>
              </ul>
            </div>
          )}
        </div>
      )}
      
      {/* Instructions */}
      <div className="instructions" style={{marginTop: '30px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px'}}>
        <h3>Instructions</h3>
        <ol>
          <li><strong>Upload:</strong> Select and upload your YAML requirements file</li>
          <li><strong>Choose Mode:</strong>
            <ul style={{marginTop: '5px'}}>
              <li><strong>Enhanced:</strong> Automatic iterations, final merge, immediate download</li>
              <li><strong>Standard:</strong> Async processing, manual iteration downloads</li>
            </ul>
          </li>
          <li><strong>Generate:</strong> Click to start code generation</li>
          <li><strong>Download:</strong> Get your complete project or specific iterations</li>
        </ol>
      </div>
    </div>
  );
};

export default ProjectGenerator;