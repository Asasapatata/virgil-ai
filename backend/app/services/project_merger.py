# backend/app/services/project_merger.py
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import shutil
import os

logger = logging.getLogger(__name__)

class ProjectMerger:
    """
    Gestisce la combinazione di tutte le iterazioni in un risultato finale completo.
    """
    
    def __init__(self, base_output_path: str = "generated_projects"):
        self.base_output_path = Path(base_output_path)
        logger.info("ProjectMerger initialized")
    
    def merge_all_iterations(self, 
                           project_id: str, 
                           iterations: List[int]) -> Dict[str, str]:
        """
        Combina tutte le iterazioni in un set completo di file finali.
        
        Args:
            project_id: ID del progetto
            iterations: Lista delle iterazioni da combinare (es: [1, 2, 3])
            
        Returns:
            Dict con tutti i file finali combinati
        """
        logger.info(f"Merging iterations {iterations} for project {project_id}")
        
        final_files = {}
        
        # 1. Inizia con i file dell'iterazione base (iter-1)
        base_iteration = min(iterations) if iterations else 1
        base_files = self._load_iteration_files(project_id, base_iteration)
        final_files.update(base_files)
        
        # 2. Applica le modifiche di ogni iterazione successiva
        for iteration in sorted(iterations[1:]):
            iteration_files = self._load_iteration_files(project_id, iteration)
            
            # Sovrascrivi/aggiungi i file modificati
            for file_path, content in iteration_files.items():
                if file_path in final_files:
                    logger.info(f"Updating {file_path} from iteration {iteration}")
                else:
                    logger.info(f"Adding new file {file_path} from iteration {iteration}")
                final_files[file_path] = content
        
        # 3. Salva il risultato finale
        self._save_final_project(project_id, final_files)
        
        logger.info(f"Final project created with {len(final_files)} files")
        return final_files
    
    def _load_iteration_files(self, project_id: str, iteration: int) -> Dict[str, str]:
        """Carica tutti i file di una specifica iterazione"""
        iteration_path = self.base_output_path / project_id / f"iter-{iteration}"
        files = {}
        
        if not iteration_path.exists():
            logger.warning(f"Iteration path not found: {iteration_path}")
            return files
        
        # Leggi tutti i file ricorsivamente
        for file_path in iteration_path.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(iteration_path)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files[str(relative_path)] = f.read()
                except Exception as e:
                    logger.error(f"Error reading {file_path}: {e}")
        
        logger.info(f"Loaded {len(files)} files from iteration {iteration}")
        return files
    
    def _save_final_project(self, project_id: str, final_files: Dict[str, str]):
        """Salva il progetto finale nella cartella 'final'"""
        final_path = self.base_output_path / project_id / "final"
        
        # Rimuovi la cartella finale esistente se presente
        if final_path.exists():
            shutil.rmtree(final_path)
        
        # Crea la cartella finale
        final_path.mkdir(parents=True, exist_ok=True)
        
        # Salva tutti i file
        for file_path, content in final_files.items():
            full_path = final_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                logger.error(f"Error saving {full_path}: {e}")
        
        # Crea un summary file
        self._create_project_summary(final_path, final_files)
        
        logger.info(f"Final project saved to {final_path}")
    
    def _create_project_summary(self, final_path: Path, final_files: Dict[str, str]):
        """Crea un file di riepilogo del progetto finale"""
        summary = {
            "total_files": len(final_files),
            "file_structure": self._build_file_tree(final_files),
            "file_types": self._analyze_file_types(final_files),
            "generated_at": self._get_current_timestamp()
        }
        
        summary_path = final_path / "PROJECT_SUMMARY.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
    
    def _build_file_tree(self, files: Dict[str, str]) -> Dict[str, Any]:
        """Costruisce un albero della struttura dei file"""
        tree = {}
        
        for file_path in sorted(files.keys()):
            parts = file_path.split('/')
            current = tree
            
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Ultima parte è il file
            current[parts[-1]] = f"<file: {len(files[file_path])} chars>"
        
        return tree
    
    def _analyze_file_types(self, files: Dict[str, str]) -> Dict[str, int]:
        """Analizza i tipi di file nel progetto"""
        file_types = {}
        
        for file_path in files.keys():
            if '.' in file_path:
                extension = file_path.split('.')[-1].lower()
                file_types[extension] = file_types.get(extension, 0) + 1
            else:
                file_types['no_extension'] = file_types.get('no_extension', 0) + 1
        
        return file_types
    
    def _get_current_timestamp(self) -> str:
        """Ottieni timestamp corrente"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_final_project_path(self, project_id: str) -> Path:
        """Ottieni il percorso del progetto finale"""
        return self.base_output_path / project_id / "final"
    
    def cleanup_iterations(self, project_id: str, keep_final: bool = True):
        """
        Pulisce le cartelle delle iterazioni, mantenendo solo il risultato finale.
        Utile per risparmiare spazio dopo aver completato un progetto.
        """
        project_path = self.base_output_path / project_id
        
        if not project_path.exists():
            logger.warning(f"Project path not found: {project_path}")
            return
        
        # Trova tutte le cartelle iter-*
        for iter_dir in project_path.glob("iter-*"):
            if iter_dir.is_dir():
                shutil.rmtree(iter_dir)
                logger.info(f"Removed iteration directory: {iter_dir}")
        
        if keep_final:
            logger.info(f"Cleanup completed, kept final directory for {project_id}")
        else:
            final_dir = project_path / "final"
            if final_dir.exists():
                shutil.rmtree(final_dir)
            logger.info(f"Full cleanup completed for {project_id}")

# backend/app/services/enhanced_code_generator.py
# Estensione del CodeGenerator per integrare il ProjectMerger

from .code_generator import CodeGenerator
from .project_merger import ProjectMerger

class EnhancedCodeGenerator(CodeGenerator):
    """
    CodeGenerator avanzato con capacità di merge automatico
    """
    
    def __init__(self, llm_service, output_path: str = "generated_projects"):
        super().__init__(llm_service)
        self.output_path = output_path
        self.merger = ProjectMerger(output_path)
        self.project_iterations = {}  # Track iterations per project
    
    async def generate_complete_project(self,
                                      project_id: str,
                                      requirements: Dict[str, Any],
                                      provider: str,
                                      max_iterations: int = 5) -> Dict[str, Any]:
        """
        Genera un progetto completo attraverso iterazioni multiple e crea il risultato finale.
        
        Returns:
            Dict contenente:
            - final_files: tutti i file del progetto finale
            - iterations_made: numero di iterazioni eseguite
            - final_path: percorso del progetto finale
            - summary: riepilogo del progetto
        """
        logger.info(f"Starting complete project generation for {project_id}")
        
        # 1. Prima iterazione: genera il progetto base
        current_files = await self.generate_code(requirements, provider, 1)
        self._save_iteration(project_id, 1, current_files)
        iterations_made = [1]
        
        # 2. Simula/esegui test e raccogli errori
        # (Qui dovresti integrare con il tuo sistema di testing)
        for iteration in range(2, max_iterations + 1):
            # Simula la ricerca di errori (sostituisci con logica reale)
            errors = self._simulate_find_errors(current_files, iteration)
            
            if not errors:
                logger.info(f"No errors found, stopping at iteration {iteration - 1}")
                break
            
            # Genera miglioramenti incrementali
            improved_files, changes = await self.generate_iterative_improvement(
                requirements, provider, iteration, errors, current_files
            )
            
            if not improved_files:
                logger.info(f"No improvements generated for iteration {iteration}")
                break
            
            # Salva l'iterazione
            self._save_iteration(project_id, iteration, improved_files)
            iterations_made.append(iteration)
            
            # Aggiorna i file correnti (merge manuale temporaneo)
            current_files.update(improved_files)
            
            logger.info(f"Iteration {iteration} completed with {len(changes)} changes")
        
        # 3. Crea il progetto finale combinando tutte le iterazioni
        final_files = self.merger.merge_all_iterations(project_id, iterations_made)
        final_path = self.merger.get_final_project_path(project_id)
        
        # 4. Crea summary
        summary = {
            "project_id": project_id,
            "iterations_completed": len(iterations_made),
            "total_files": len(final_files),
            "final_path": str(final_path),
            "requirements": requirements
        }
        
        return {
            "final_files": final_files,
            "iterations_made": iterations_made,
            "final_path": final_path,
            "summary": summary
        }
    
    def _save_iteration(self, project_id: str, iteration: int, files: Dict[str, str]):
        """Salva i file di un'iterazione specifica"""
        iteration_path = Path(self.output_path) / project_id / f"iter-{iteration}"
        iteration_path.mkdir(parents=True, exist_ok=True)
        
        for file_path, content in files.items():
            full_path = iteration_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        logger.info(f"Saved iteration {iteration} with {len(files)} files")
    
    def _simulate_find_errors(self, files: Dict[str, str], iteration: int) -> List[Dict[str, Any]]:
        """
        Simula la ricerca di errori (sostituisci con la tua logica reale).
        Dovrebbe integrare con il sistema di testing/compilation.
        """
        # Esempio di simulazione - in realtà dovresti:
        # 1. Compilare il codice
        # 2. Eseguire test
        # 3. Raccogliere errori reali
        
        if iteration >= 4:  # Simula che dopo 3 iterazioni non ci sono più errori
            return []
        
        # Simula alcuni errori per demo
        simulated_errors = [
            {
                "file": "src/components/Header.tsx",
                "line": 15,
                "message": "Type 'string' is not assignable to type 'number'"
            },
            {
                "file": "src/utils/api.ts", 
                "line": 8,
                "message": "Cannot find module 'axios'"
            }
        ]
        
        return simulated_errors[:iteration-1]  # Meno errori ad ogni iterazione