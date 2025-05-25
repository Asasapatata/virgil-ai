# backend/app/services/output_manager.py
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from app.services.workspace_environment import WorkspaceEnvironment

logger = logging.getLogger(__name__)

@dataclass
class IterationResults:
    """Risultati strutturati di una iterazione"""
    iteration: int
    status: str  # "success", "failed", "partial"
    validation_errors: int
    compilation_success: bool
    test_results: Dict[str, Any]
    code_files_count: int
    test_files_count: int
    duration: float
    errors_fixed: List[str]
    improvements: List[str]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class OutputManager:
    """Gestisce output finale e log consolidati senza mantenere iterazioni intermedie"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.workspace_path = project_path / "workspace"
        self.final_path = project_path / "final"
        self.logs_path = project_path / "logs"
        self.reports_path = project_path / "reports"
        
        self._setup_directories()
        self._initialize_logs()
    
    def _setup_directories(self):
        """Crea struttura directory necessaria"""
        self.logs_path.mkdir(parents=True, exist_ok=True)
        self.reports_path.mkdir(parents=True, exist_ok=True)
        
        # Pulizia workspace precedente se esiste
        if self.workspace_path.exists():
            shutil.rmtree(self.workspace_path)
    
    def _initialize_logs(self):
        """Inizializza file di log se non esistono"""
        
        # Log principale iterazioni
        iterations_log = self.logs_path / "iterations.log"
        if not iterations_log.exists():
            with open(iterations_log, 'w') as f:
                f.write(f"=== PROJECT GENERATION LOG ===\n")
                f.write(f"Started: {datetime.now().isoformat()}\n")
                f.write(f"Project: {self.project_path.name}\n\n")
        
        # Storia test strutturata
        test_history_file = self.logs_path / "test_history.json"
        if not test_history_file.exists():
            with open(test_history_file, 'w') as f:
                json.dump({"iterations": [], "summary": {}}, f, indent=2)
        
        # Evoluzione errori
        error_evolution_file = self.logs_path / "error_evolution.json"
        if not error_evolution_file.exists():
            with open(error_evolution_file, 'w') as f:
                json.dump({"error_timeline": [], "resolution_stats": {}}, f, indent=2)
    
    def create_workspace(self) -> 'WorkspaceEnvironment':
        """Crea ambiente di lavoro pulito per iterazione"""
        from app.services.workspace_environment import WorkspaceEnvironment
        
        workspace = WorkspaceEnvironment(self.workspace_path)
        workspace.clean_and_prepare()
        return workspace
    
    def update_final_code(self, code_files: Dict[str, str], iteration: int, force: bool = False):
        """Aggiorna il codice finale solo se migliora la qualità"""
        
        should_update = force
        
        if not force and self.final_path.exists():
            # Logica per decidere se aggiornare basata su qualità
            current_quality = self._assess_code_quality(self.final_path)
            new_quality = self._assess_code_quality_from_files(code_files)
            
            should_update = new_quality >= current_quality
            
            logger.info(f"Code quality assessment - Current: {current_quality}, New: {new_quality}, Update: {should_update}")
        else:
            should_update = True
        
        if should_update:
            # Rimuovi versione precedente
            if self.final_path.exists():
                shutil.rmtree(self.final_path)
            
            # Salva nuova versione
            self.final_path.mkdir(parents=True, exist_ok=True)
            for file_path, content in code_files.items():
                full_path = self.final_path / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content, encoding='utf-8')
            
            logger.info(f"Updated final code with {len(code_files)} files from iteration {iteration}")
            
            # Log l'aggiornamento
            self._log_final_update(iteration, len(code_files))
        else:
            logger.info(f"Skipped final code update - quality did not improve (iteration {iteration})")
    
    def log_iteration(self, iteration: int, results: IterationResults):
        """Registra risultati iterazione nei log consolidati"""
        
        logger.info(f"Logging results for iteration {iteration}")
        
        # 1. Append al log principale
        with open(self.logs_path / "iterations.log", 'a') as f:
            f.write(f"\n=== ITERATION {iteration} ===\n")
            f.write(f"Timestamp: {results.timestamp}\n")
            f.write(f"Status: {results.status}\n")
            f.write(f"Duration: {results.duration:.2f}s\n")
            f.write(f"Files Generated: {results.code_files_count}\n")
            f.write(f"Test Files: {results.test_files_count}\n")
            f.write(f"Validation Errors: {results.validation_errors}\n")
            f.write(f"Compilation Success: {results.compilation_success}\n")
            f.write(f"Test Success: {results.test_results.get('success', False)}\n")
            
            if results.errors_fixed:
                f.write("Errors Fixed:\n")
                for error in results.errors_fixed:
                    f.write(f"  - {error}\n")
            
            if results.improvements:
                f.write("Improvements:\n")
                for improvement in results.improvements:
                    f.write(f"  + {improvement}\n")
            
            # Test details summary
            if results.test_results:
                f.write("Test Results Summary:\n")
                for test_type, result in results.test_results.items():
                    if test_type != 'success' and result:
                        success = result.get('success', False) if isinstance(result, dict) else result
                        f.write(f"  {test_type}: {'PASS' if success else 'FAIL'}\n")
            
            f.write("-" * 50 + "\n")
        
        # 2. Aggiorna storia test strutturata
        self._update_test_history(iteration, results)
        
        # 3. Aggiorna evoluzione errori
        self._update_error_evolution(iteration, results)
        
        # 4. Aggiorna statistiche prestazioni
        self._update_performance_stats(iteration, results)
    
    def _update_test_history(self, iteration: int, results: IterationResults):
        """Aggiorna storia test strutturata"""
        test_history_file = self.logs_path / "test_history.json"
        
        try:
            with open(test_history_file, 'r') as f:
                test_history = json.load(f)
        except:
            test_history = {"iterations": [], "summary": {}}
        
        # Aggiungi questa iterazione
        iteration_data = {
            "iteration": iteration,
            "timestamp": results.timestamp,
            "status": results.status,
            "duration": results.duration,
            "test_results": results.test_results,
            "validation_errors": results.validation_errors,
            "compilation_success": results.compilation_success,
            "files_count": results.code_files_count
        }
        
        test_history["iterations"].append(iteration_data)
        
        # Aggiorna summary
        test_history["summary"] = {
            "total_iterations": len(test_history["iterations"]),
            "successful_iterations": len([i for i in test_history["iterations"] if i["status"] == "success"]),
            "total_duration": sum([i["duration"] for i in test_history["iterations"]]),
            "avg_duration": sum([i["duration"] for i in test_history["iterations"]]) / len(test_history["iterations"]),
            "final_status": results.status,
            "last_updated": results.timestamp
        }
        
        with open(test_history_file, 'w') as f:
            json.dump(test_history, f, indent=2)
    
    def _update_error_evolution(self, iteration: int, results: IterationResults):
        """Aggiorna evoluzione errori nel tempo"""
        error_evolution_file = self.logs_path / "error_evolution.json"
        
        try:
            with open(error_evolution_file, 'r') as f:
                error_evolution = json.load(f)
        except:
            error_evolution = {"error_timeline": [], "resolution_stats": {}}
        
        # Aggiungi snapshot errori questa iterazione
        error_snapshot = {
            "iteration": iteration,
            "timestamp": results.timestamp,
            "validation_errors": results.validation_errors,
            "compilation_success": results.compilation_success,
            "test_failures": self._count_test_failures(results.test_results),
            "errors_fixed": len(results.errors_fixed),
            "total_active_errors": results.validation_errors + (0 if results.compilation_success else 1) + self._count_test_failures(results.test_results)
        }
        
        error_evolution["error_timeline"].append(error_snapshot)
        
        # Calcola statistiche risoluzione
        if len(error_evolution["error_timeline"]) > 1:
            prev = error_evolution["error_timeline"][-2]
            current = error_snapshot
            
            error_evolution["resolution_stats"] = {
                "validation_errors_trend": "decreasing" if current["validation_errors"] < prev["validation_errors"] else "increasing" if current["validation_errors"] > prev["validation_errors"] else "stable",
                "compilation_improved": current["compilation_success"] and not prev["compilation_success"],
                "test_failures_trend": "decreasing" if current["test_failures"] < prev["test_failures"] else "increasing" if current["test_failures"] > prev["test_failures"] else "stable",
                "overall_progress": "improving" if current["total_active_errors"] < prev["total_active_errors"] else "regressing" if current["total_active_errors"] > prev["total_active_errors"] else "stable"
            }
        
        with open(error_evolution_file, 'w') as f:
            json.dump(error_evolution, f, indent=2)
    
    def _update_performance_stats(self, iteration: int, results: IterationResults):
        """Aggiorna statistiche prestazioni"""
        performance_file = self.logs_path / "performance_stats.json"
        
        try:
            with open(performance_file, 'r') as f:
                stats = json.load(f)
        except:
            stats = {"iterations": [], "averages": {}}
        
        # Aggiungi dati prestazioni
        perf_data = {
            "iteration": iteration,
            "timestamp": results.timestamp,
            "duration": results.duration,
            "files_generated": results.code_files_count,
            "test_files": results.test_files_count,
            "files_per_second": results.code_files_count / results.duration if results.duration > 0 else 0
        }
        
        stats["iterations"].append(perf_data)
        
        # Calcola medie
        all_durations = [i["duration"] for i in stats["iterations"]]
        all_files = [i["files_generated"] for i in stats["iterations"]]
        
        stats["averages"] = {
            "avg_duration": sum(all_durations) / len(all_durations),
            "avg_files_per_iteration": sum(all_files) / len(all_files),
            "avg_files_per_second": sum([i["files_per_second"] for i in stats["iterations"]]) / len(stats["iterations"]),
            "fastest_iteration": min(all_durations),
            "slowest_iteration": max(all_durations),
            "total_files_generated": sum(all_files)
        }
        
        with open(performance_file, 'w') as f:
            json.dump(stats, f, indent=2)
    
    def _count_test_failures(self, test_results: Dict[str, Any]) -> int:
        """Conta il numero di test failures"""
        if not test_results:
            return 0
        
        failures = 0
        for test_type, result in test_results.items():
            if test_type != 'success' and isinstance(result, dict):
                if not result.get('success', True):
                    failures += 1
        
        return failures
    
    def _assess_code_quality(self, code_path: Path) -> float:
        """Valuta qualità del codice esistente (0-100)"""
        if not code_path.exists():
            return 0.0
        
        try:
            files = list(code_path.rglob("*"))
            code_files = [f for f in files if f.is_file() and f.suffix in ['.py', '.js', '.ts', '.tsx', '.jsx']]
            
            if not code_files:
                return 0.0
            
            # Metriche di qualità semplici
            quality_score = 50.0  # Base score
            
            # Bonus per varietà di file
            file_types = set(f.suffix for f in code_files)
            quality_score += len(file_types) * 5
            
            # Bonus per struttura organizzata
            directories = set(f.parent for f in code_files)
            if len(directories) > 2:
                quality_score += 10
            
            # Bonus per presenza di test
            test_files = [f for f in files if 'test' in f.name.lower()]
            if test_files:
                quality_score += 20
            
            # Bonus per file di configurazione
            config_files = [f for f in files if f.name in ['package.json', 'requirements.txt', 'tsconfig.json']]
            quality_score += len(config_files) * 5
            
            return min(quality_score, 100.0)
            
        except Exception as e:
            logger.warning(f"Error assessing code quality: {e}")
            return 0.0
    
    def _assess_code_quality_from_files(self, code_files: Dict[str, str]) -> float:
        """Valuta qualità del codice da dizionario files (0-100)"""
        if not code_files:
            return 0.0
        
        quality_score = 50.0  # Base score
        
        # Bonus per varietà di file
        file_extensions = set(Path(f).suffix for f in code_files.keys())
        quality_score += len(file_extensions) * 5
        
        # Bonus per struttura organizzata
        directories = set(str(Path(f).parent) for f in code_files.keys())
        if len(directories) > 2:
            quality_score += 10
        
        # Bonus per presenza di test
        test_files = [f for f in code_files.keys() if 'test' in f.lower()]
        if test_files:
            quality_score += 20
        
        # Bonus per file di configurazione
        config_files = [f for f in code_files.keys() if Path(f).name in ['package.json', 'requirements.txt', 'tsconfig.json']]
        quality_score += len(config_files) * 5
        
        # Bonus per dimensione contenuto (codice più sostanzioso)
        avg_file_size = sum(len(content) for content in code_files.values()) / len(code_files)
        if avg_file_size > 500:  # File con contenuto sostanzioso
            quality_score += 10
        
        return min(quality_score, 100.0)
    
    def _log_final_update(self, iteration: int, files_count: int):
        """Log dell'aggiornamento del codice finale"""
        with open(self.logs_path / "iterations.log", 'a') as f:
            f.write(f"\n>>> FINAL CODE UPDATED from iteration {iteration} ({files_count} files) <<<\n")
    
    def finalize_project(self, final_results: Dict[str, Any]) -> Dict[str, Any]:
        """Crea report finali e pulisce workspace"""
        
        logger.info("Finalizing project and generating reports")
        
        # 1. Conta file finali
        final_files_count = 0
        if self.final_path.exists():
            final_files_count = len([f for f in self.final_path.rglob("*") if f.is_file()])
        
        # 2. Carica statistiche dai log
        stats = self._load_consolidated_stats()
        
        # 3. Crea report finale completo
        final_summary = {
            "project_completed_at": datetime.now().isoformat(),
            "project_id": self.project_path.name,
            "generation_results": final_results,
            "statistics": stats,
            "final_output": {
                "files_count": final_files_count,
                "final_path": str(self.final_path.relative_to(self.project_path)),
                "logs_path": str(self.logs_path.relative_to(self.project_path)),
                "reports_path": str(self.reports_path.relative_to(self.project_path))
            },
            "quality_assessment": {
                "final_code_quality": self._assess_code_quality(self.final_path),
                "structure_organized": final_files_count > 5,
                "has_tests": self._has_test_files(),
                "has_config": self._has_config_files()
            }
        }
        
        # 4. Salva report finale
        with open(self.reports_path / "final_summary.json", 'w') as f:
            json.dump(final_summary, f, indent=2)
        
        # 5. Crea report di qualità separato
        self._create_quality_report(stats)
        
        # 6. Crea README per navigazione
        self._create_navigation_readme()
        
        # 7. Pulisci workspace temporaneo
        if self.workspace_path.exists():
            shutil.rmtree(self.workspace_path)
            logger.info("Cleaned up temporary workspace")
        
        # 8. Log finale
        with open(self.logs_path / "iterations.log", 'a') as f:
            f.write(f"\n=== PROJECT FINALIZED ===\n")
            f.write(f"Completed: {final_summary['project_completed_at']}\n")
            f.write(f"Final Status: {final_results.get('status', 'unknown')}\n")
            f.write(f"Total Iterations: {stats.get('total_iterations', 0)}\n")
            f.write(f"Final Files: {final_files_count}\n")
            f.write(f"Code Quality Score: {final_summary['quality_assessment']['final_code_quality']:.1f}/100\n")
            f.write("=" * 50 + "\n")
        
        logger.info(f"Project finalized: {final_files_count} files in {self.final_path}")
        
        return {
            "final_summary": final_summary,
            "final_path": str(self.final_path),
            "logs_path": str(self.logs_path),
            "reports_path": str(self.reports_path)
        }
    
    def _load_consolidated_stats(self) -> Dict[str, Any]:
        """Carica tutte le statistiche consolidate"""
        stats = {}
        
        # Test history
        try:
            with open(self.logs_path / "test_history.json", 'r') as f:
                test_history = json.load(f)
                stats.update(test_history.get("summary", {}))
        except:
            pass
        
        # Error evolution
        try:
            with open(self.logs_path / "error_evolution.json", 'r') as f:
                error_evolution = json.load(f)
                if error_evolution.get("error_timeline"):
                    final_errors = error_evolution["error_timeline"][-1]
                    stats["final_error_state"] = final_errors
                    stats["error_resolution"] = error_evolution.get("resolution_stats", {})
        except:
            pass
        
        # Performance stats
        try:
            with open(self.logs_path / "performance_stats.json", 'r') as f:
                performance = json.load(f)
                stats["performance"] = performance.get("averages", {})
        except:
            pass
        
        return stats
    
    def _create_quality_report(self, stats: Dict[str, Any]):
        """Crea report dettagliato di qualità"""
        quality_report = {
            "generated_at": datetime.now().isoformat(),
            "code_quality": {
                "final_score": self._assess_code_quality(self.final_path),
                "has_organized_structure": self._has_organized_structure(),
                "has_tests": self._has_test_files(),
                "has_configuration": self._has_config_files(),
                "file_diversity": self._assess_file_diversity()
            },
            "generation_quality": {
                "iterations_efficiency": stats.get("successful_iterations", 0) / stats.get("total_iterations", 1),
                "error_resolution_rate": self._calculate_error_resolution_rate(stats),
                "average_iteration_time": stats.get("performance", {}).get("avg_duration", 0),
                "files_generation_rate": stats.get("performance", {}).get("avg_files_per_second", 0)
            },
            "recommendations": self._generate_quality_recommendations(stats)
        }
        
        with open(self.reports_path / "quality_report.json", 'w') as f:
            json.dump(quality_report, f, indent=2)
    
    def _create_navigation_readme(self):
        """Crea README per navigare l'output del progetto"""
        readme_content = f"""# Generated Project: {self.project_path.name}

## 📁 Project Structure

```
{self.project_path.name}/
├── final/                    # 🎯 Final generated code
│   └── {self.project_path.name}/     # Your application code
├── logs/                     # 📊 Generation logs
│   ├── iterations.log        # Detailed iteration log
│   ├── test_history.json     # Test results history
│   ├── error_evolution.json  # Error tracking
│   └── performance_stats.json # Performance metrics
└── reports/                  # 📋 Summary reports
    ├── final_summary.json    # Complete project summary
    ├── quality_report.json   # Code quality assessment
    └── README.md            # This file
```

## 🚀 Quick Start

1. **Your Generated Code**: Check the `final/` directory
2. **Logs**: Review `logs/iterations.log` for detailed generation process
3. **Summary**: See `reports/final_summary.json` for complete overview

## 📊 Generation Statistics

- **Project Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Final Code Location**: `final/{self.project_path.name}/`
- **Logs Location**: `logs/`
- **Reports Location**: `reports/`

## 🔍 Understanding the Logs

- **iterations.log**: Human-readable log of each generation iteration
- **test_history.json**: Structured test results from all iterations  
- **error_evolution.json**: How errors were detected and resolved
- **performance_stats.json**: Performance metrics and timing data

## 💡 Tips

- All intermediate iteration files have been cleaned up to save space
- Only the final, best-quality code is kept in `final/`
- Logs contain complete history of the generation process
- Reports provide summarized insights and quality metrics
"""
        
        with open(self.reports_path / "README.md", 'w') as f:
            f.write(readme_content)
    
    def _has_organized_structure(self) -> bool:
        """Verifica se il codice ha una struttura organizzata"""
        if not self.final_path.exists():
            return False
        
        directories = set()
        for file_path in self.final_path.rglob("*"):
            if file_path.is_file():
                directories.add(str(file_path.parent))
        
        return len(directories) > 2  # Più di 2 directory = struttura organizzata
    
    def _has_test_files(self) -> bool:
        """Verifica presenza di file di test"""
        if not self.final_path.exists():
            return False
        
        test_files = [f for f in self.final_path.rglob("*") if 'test' in f.name.lower()]
        return len(test_files) > 0
    
    def _has_config_files(self) -> bool:
        """Verifica presenza di file di configurazione"""
        if not self.final_path.exists():
            return False
        
        config_names = ['package.json', 'requirements.txt', 'tsconfig.json', '.env', 'Dockerfile']
        for config_name in config_names:
            if (self.final_path / config_name).exists():
                return True
        
        return False
    
    def _assess_file_diversity(self) -> Dict[str, int]:
        """Valuta diversità dei tipi di file"""
        if not self.final_path.exists():
            return {}
        
        file_types = {}
        for file_path in self.final_path.rglob("*"):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                file_types[ext] = file_types.get(ext, 0) + 1
        
        return file_types
    
    def _calculate_error_resolution_rate(self, stats: Dict[str, Any]) -> float:
        """Calcola tasso di risoluzione errori"""
        final_error_state = stats.get("final_error_state", {})
        
        if not final_error_state:
            return 0.0
        
        total_final_errors = final_error_state.get("total_active_errors", 1)
        
        # Se ci sono 0 errori finali, tasso = 100%
        if total_final_errors == 0:
            return 1.0
        
        # Altrimenti calcola basato su progressi
        resolution_stats = stats.get("error_resolution", {})
        if resolution_stats.get("overall_progress") == "improving":
            return 0.8  # Buon progresso
        elif resolution_stats.get("overall_progress") == "stable":
            return 0.5  # Progresso moderato
        else:
            return 0.2  # Progresso limitato
    
    def _generate_quality_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Genera raccomandazioni basate su qualità e statistiche"""
        recommendations = []
        
        # Raccomandazioni basate su qualità codice
        if not self._has_test_files():
            recommendations.append("Consider adding test files to improve code reliability")
        
        if not self._has_config_files():
            recommendations.append("Add configuration files (package.json, requirements.txt) for better dependency management")
        
        if not self._has_organized_structure():
            recommendations.append("Organize code into logical directories for better maintainability")
        
        # Raccomandazioni basate su performance
        performance = stats.get("performance", {})
        avg_duration = performance.get("avg_duration", 0)
        
        if avg_duration > 120:  # > 2 minuti per iterazione
            recommendations.append("Generation time is high - consider simplifying requirements for faster iterations")
        
        # Raccomandazioni basate su risoluzione errori
        error_resolution_rate = self._calculate_error_resolution_rate(stats)
        if error_resolution_rate < 0.5:
            recommendations.append("Error resolution rate is low - review requirements clarity and complexity")
        
        if not recommendations:
            recommendations.append("Code quality looks good! Consider adding more comprehensive tests.")
        
        return recommendations