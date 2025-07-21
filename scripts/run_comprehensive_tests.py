#!/usr/bin/env python3
"""
Comprehensive Test Runner for Lexicon Enhanced Features
Runs both Python and TypeScript tests with detailed reporting
"""

import asyncio
import subprocess
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import tempfile
import shutil

@dataclass
class TestResult:
    """Test execution result"""
    name: str
    status: str  # 'passed', 'failed', 'skipped'
    duration: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

@dataclass
class TestSuite:
    """Test suite configuration and results"""
    name: str
    command: List[str]
    working_directory: str
    results: List[TestResult]
    total_duration: float = 0.0
    passed: int = 0
    failed: int = 0
    skipped: int = 0

class ComprehensiveTestRunner:
    """Runs all test suites and generates comprehensive reports"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.test_suites: List[TestSuite] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.setup_test_suites()
    
    def setup_test_suites(self):
        """Configure all test suites"""
        
        # Python integration tests
        python_engine_dir = self.project_root / "python-engine"
        if python_engine_dir.exists():
            self.test_suites.append(TestSuite(
                name="Python Enhanced Features Integration",
                command=["python", "-m", "pytest", "tests/test_enhanced_features_integration.py", "-v", "--tb=short"],
                working_directory=str(python_engine_dir),
                results=[]
            ))
            
            # Individual Python component tests
            self.test_suites.append(TestSuite(
                name="Python Semantic Search Tests",
                command=["python", "-m", "pytest", "tests/test_enhanced_features_integration.py::TestSemanticSearchIntegration", "-v"],
                working_directory=str(python_engine_dir),
                results=[]
            ))
            
            self.test_suites.append(TestSuite(
                name="Python Processing Pipeline Tests",
                command=["python", "-m", "pytest", "tests/test_enhanced_features_integration.py::TestProcessingPipelineIntegration", "-v"],
                working_directory=str(python_engine_dir),
                results=[]
            ))
            
            self.test_suites.append(TestSuite(
                name="Python Error Handling Tests", 
                command=["python", "-m", "pytest", "tests/test_enhanced_features_integration.py::TestErrorHandlingIntegration", "-v"],
                working_directory=str(python_engine_dir),
                results=[]
            ))
            
            self.test_suites.append(TestSuite(
                name="Python Backup System Tests",
                command=["python", "-m", "pytest", "tests/test_enhanced_features_integration.py::TestBackupRestoreIntegration", "-v"],
                working_directory=str(python_engine_dir),
                results=[]
            ))
        
        # TypeScript/React tests
        self.test_suites.append(TestSuite(
            name="React Semantic Search Component",
            command=["npm", "run", "test", "src/test/components/SemanticSearch.test.tsx"],
            working_directory=str(self.project_root),
            results=[]
        ))
        
        self.test_suites.append(TestSuite(
            name="Enhanced Features E2E Integration",
            command=["npm", "run", "test", "src/test/integration/EnhancedFeaturesE2E.test.tsx"],
            working_directory=str(self.project_root),
            results=[]
        ))
        
        # Existing test suites
        self.test_suites.append(TestSuite(
            name="All React Component Tests",
            command=["npm", "run", "test", "--", "--run"],
            working_directory=str(self.project_root),
            results=[]
        ))
        
        # Rust tests (if available)
        src_tauri_dir = self.project_root / "src-tauri"
        if src_tauri_dir.exists():
            self.test_suites.append(TestSuite(
                name="Rust Backend Tests",
                command=["cargo", "test"],
                working_directory=str(src_tauri_dir),
                results=[]
            ))
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites and return comprehensive results"""
        print("🚀 Starting Comprehensive Test Suite for Enhanced Lexicon Features")
        print("=" * 70)
        
        self.start_time = datetime.now()
        overall_results = {
            "start_time": self.start_time.isoformat(),
            "test_suites": [],
            "summary": {
                "total_suites": len(self.test_suites),
                "passed_suites": 0,
                "failed_suites": 0,
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "skipped_tests": 0
            }
        }
        
        for suite in self.test_suites:
            print(f"\n📋 Running: {suite.name}")
            print("-" * 50)
            
            suite_result = await self.run_test_suite(suite)
            overall_results["test_suites"].append(suite_result)
            
            # Update summary
            if suite.failed == 0:
                overall_results["summary"]["passed_suites"] += 1
            else:
                overall_results["summary"]["failed_suites"] += 1
            
            overall_results["summary"]["total_tests"] += len(suite.results)
            overall_results["summary"]["passed_tests"] += suite.passed
            overall_results["summary"]["failed_tests"] += suite.failed
            overall_results["summary"]["skipped_tests"] += suite.skipped
        
        self.end_time = datetime.now()
        overall_results["end_time"] = self.end_time.isoformat()
        overall_results["total_duration"] = (self.end_time - self.start_time).total_seconds()
        
        self.print_summary(overall_results)
        await self.generate_reports(overall_results)
        
        return overall_results
    
    async def run_test_suite(self, suite: TestSuite) -> Dict[str, Any]:
        """Run a single test suite"""
        start_time = time.time()
        
        try:
            # Run the test command
            result = subprocess.run(
                suite.command,
                cwd=suite.working_directory,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            suite.total_duration = time.time() - start_time
            
            # Parse test results based on the tool
            if "pytest" in suite.command[0] or "python" in suite.command[0]:
                self.parse_pytest_output(suite, result)
            elif "npm" in suite.command[0]:
                self.parse_vitest_output(suite, result)
            elif "cargo" in suite.command[0]:
                self.parse_cargo_output(suite, result)
            else:
                # Generic parsing
                self.parse_generic_output(suite, result)
            
            print(f"✅ {suite.name}: {suite.passed} passed, {suite.failed} failed, {suite.skipped} skipped")
            if suite.failed > 0:
                print(f"❌ Failures in {suite.name}")
                if result.stderr:
                    print(f"Error output: {result.stderr[:500]}...")
            
        except subprocess.TimeoutExpired:
            suite.results.append(TestResult(
                name=suite.name,
                status="failed",
                duration=time.time() - start_time,
                error_message="Test suite timed out"
            ))
            suite.failed = 1
            print(f"⏰ {suite.name}: TIMEOUT")
            
        except Exception as e:
            suite.results.append(TestResult(
                name=suite.name,
                status="failed", 
                duration=time.time() - start_time,
                error_message=str(e)
            ))
            suite.failed = 1
            print(f"💥 {suite.name}: ERROR - {e}")
        
        return {
            "name": suite.name,
            "duration": suite.total_duration,
            "passed": suite.passed,
            "failed": suite.failed,
            "skipped": suite.skipped,
            "results": [
                {
                    "name": r.name,
                    "status": r.status,
                    "duration": r.duration,
                    "error": r.error_message
                }
                for r in suite.results
            ]
        }
    
    def parse_pytest_output(self, suite: TestSuite, result: subprocess.CompletedProcess):
        """Parse pytest output"""
        output = result.stdout + result.stderr
        
        # Look for test results in pytest output
        lines = output.split('\n')
        current_test = None
        
        for line in lines:
            line = line.strip()
            
            # Test start/result patterns
            if '::' in line and ('PASSED' in line or 'FAILED' in line or 'SKIPPED' in line):
                parts = line.split('::')
                if len(parts) >= 2:
                    test_name = parts[-1].split()[0]
                    
                    if 'PASSED' in line:
                        status = 'passed'
                        suite.passed += 1
                    elif 'FAILED' in line:
                        status = 'failed'
                        suite.failed += 1
                    else:
                        status = 'skipped'
                        suite.skipped += 1
                    
                    suite.results.append(TestResult(
                        name=test_name,
                        status=status,
                        duration=0.0  # pytest doesn't always show duration
                    ))
        
        # If no individual tests found, use overall result
        if not suite.results:
            if result.returncode == 0:
                suite.results.append(TestResult(
                    name=suite.name,
                    status='passed',
                    duration=suite.total_duration
                ))
                suite.passed = 1
            else:
                suite.results.append(TestResult(
                    name=suite.name,
                    status='failed',
                    duration=suite.total_duration,
                    error_message=result.stderr
                ))
                suite.failed = 1
    
    def parse_vitest_output(self, suite: TestSuite, result: subprocess.CompletedProcess):
        """Parse Vitest output"""
        output = result.stdout + result.stderr
        
        # Vitest shows test results differently
        if result.returncode == 0:
            # Look for test count in output
            if 'passed' in output.lower():
                suite.passed = 1
                suite.results.append(TestResult(
                    name=suite.name,
                    status='passed',
                    duration=suite.total_duration
                ))
            else:
                suite.passed = 1
                suite.results.append(TestResult(
                    name=suite.name,
                    status='passed',
                    duration=suite.total_duration
                ))
        else:
            suite.failed = 1
            suite.results.append(TestResult(
                name=suite.name,
                status='failed',
                duration=suite.total_duration,
                error_message=result.stderr
            ))
    
    def parse_cargo_output(self, suite: TestSuite, result: subprocess.CompletedProcess):
        """Parse Cargo test output"""
        output = result.stdout + result.stderr
        
        if result.returncode == 0:
            suite.passed = 1
            suite.results.append(TestResult(
                name=suite.name,
                status='passed',
                duration=suite.total_duration
            ))
        else:
            suite.failed = 1
            suite.results.append(TestResult(
                name=suite.name,
                status='failed',
                duration=suite.total_duration,
                error_message=result.stderr
            ))
    
    def parse_generic_output(self, suite: TestSuite, result: subprocess.CompletedProcess):
        """Generic output parsing"""
        if result.returncode == 0:
            suite.passed = 1
            suite.results.append(TestResult(
                name=suite.name,
                status='passed',
                duration=suite.total_duration
            ))
        else:
            suite.failed = 1
            suite.results.append(TestResult(
                name=suite.name,
                status='failed',
                duration=suite.total_duration,
                error_message=result.stderr
            ))
    
    def print_summary(self, results: Dict[str, Any]):
        """Print comprehensive test summary"""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 70)
        
        summary = results["summary"]
        
        print(f"🕐 Total Duration: {results['total_duration']:.2f} seconds")
        print(f"📦 Test Suites: {summary['total_suites']} total")
        print(f"   ✅ Passed: {summary['passed_suites']}")
        print(f"   ❌ Failed: {summary['failed_suites']}")
        
        print(f"🧪 Individual Tests: {summary['total_tests']} total")
        print(f"   ✅ Passed: {summary['passed_tests']}")
        print(f"   ❌ Failed: {summary['failed_tests']}")
        print(f"   ⏭️ Skipped: {summary['skipped_tests']}")
        
        if summary['total_tests'] > 0:
            success_rate = (summary['passed_tests'] / summary['total_tests']) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
        
        print("\n📋 Suite Details:")
        for suite_result in results["test_suites"]:
            status_icon = "✅" if suite_result["failed"] == 0 else "❌"
            print(f"   {status_icon} {suite_result['name']}: "
                  f"{suite_result['passed']}P {suite_result['failed']}F {suite_result['skipped']}S "
                  f"({suite_result['duration']:.2f}s)")
        
        # Overall status
        if summary['failed_suites'] == 0 and summary['failed_tests'] == 0:
            print("\n🎉 ALL TESTS PASSED! Enhanced features are ready for production.")
        else:
            print(f"\n⚠️ {summary['failed_suites']} suite(s) and {summary['failed_tests']} test(s) failed.")
            print("Review the failures before proceeding to production.")
    
    async def generate_reports(self, results: Dict[str, Any]):
        """Generate detailed test reports"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON report
        json_report_path = self.project_root / f"test_results_{timestamp}.json"
        with open(json_report_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # HTML report
        html_report_path = self.project_root / f"test_report_{timestamp}.html"
        await self.generate_html_report(results, html_report_path)
        
        # CI/CD friendly report
        junit_report_path = self.project_root / f"junit_results_{timestamp}.xml"
        await self.generate_junit_report(results, junit_report_path)
        
        print(f"\n📁 Reports Generated:")
        print(f"   📄 JSON: {json_report_path}")
        print(f"   🌐 HTML: {html_report_path}")
        print(f"   🔧 JUnit: {junit_report_path}")
    
    async def generate_html_report(self, results: Dict[str, Any], output_path: Path):
        """Generate HTML test report"""
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lexicon Enhanced Features Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 8px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .metric {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .suite {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }}
        .passed {{ color: #28a745; }}
        .failed {{ color: #dc3545; }}
        .skipped {{ color: #ffc107; }}
        .test-list {{ margin-top: 10px; }}
        .test-item {{ padding: 5px; margin: 2px 0; background: #f9f9f9; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Lexicon Enhanced Features Test Report</h1>
        <p>Generated: {results['start_time']}</p>
        <p>Duration: {results['total_duration']:.2f} seconds</p>
    </div>

    <div class="summary">
        <div class="metric">
            <h3>Test Suites</h3>
            <p>Total: {results['summary']['total_suites']}</p>
            <p class="passed">Passed: {results['summary']['passed_suites']}</p>
            <p class="failed">Failed: {results['summary']['failed_suites']}</p>
        </div>
        <div class="metric">
            <h3>Individual Tests</h3>
            <p>Total: {results['summary']['total_tests']}</p>
            <p class="passed">Passed: {results['summary']['passed_tests']}</p>
            <p class="failed">Failed: {results['summary']['failed_tests']}</p>
            <p class="skipped">Skipped: {results['summary']['skipped_tests']}</p>
        </div>
    </div>

    <h2>📋 Test Suite Details</h2>
"""
        
        for suite in results['test_suites']:
            status_class = 'passed' if suite['failed'] == 0 else 'failed'
            html_content += f"""
    <div class="suite">
        <h3 class="{status_class}">{suite['name']}</h3>
        <p>Duration: {suite['duration']:.2f}s | 
           Passed: {suite['passed']} | 
           Failed: {suite['failed']} | 
           Skipped: {suite['skipped']}</p>
        <div class="test-list">
"""
            
            for test in suite['results']:
                test_class = test['status']
                error_info = f" - {test['error']}" if test['error'] else ""
                html_content += f"""
            <div class="test-item {test_class}">
                {test['name']} ({test['duration']:.2f}s) - {test['status'].upper()}{error_info}
            </div>
"""
            
            html_content += "        </div>\n    </div>\n"
        
        html_content += """
</body>
</html>
"""
        
        with open(output_path, 'w') as f:
            f.write(html_content)
    
    async def generate_junit_report(self, results: Dict[str, Any], output_path: Path):
        """Generate JUnit XML report for CI/CD systems"""
        from xml.etree.ElementTree import Element, SubElement, tostring
        from xml.dom import minidom
        
        root = Element('testsuites')
        root.set('name', 'Lexicon Enhanced Features')
        root.set('tests', str(results['summary']['total_tests']))
        root.set('failures', str(results['summary']['failed_tests']))
        root.set('skipped', str(results['summary']['skipped_tests']))
        root.set('time', str(results['total_duration']))
        
        for suite_data in results['test_suites']:
            suite = SubElement(root, 'testsuite')
            suite.set('name', suite_data['name'])
            suite.set('tests', str(len(suite_data['results'])))
            suite.set('failures', str(suite_data['failed']))
            suite.set('skipped', str(suite_data['skipped']))
            suite.set('time', str(suite_data['duration']))
            
            for test_data in suite_data['results']:
                testcase = SubElement(suite, 'testcase')
                testcase.set('name', test_data['name'])
                testcase.set('classname', suite_data['name'])
                testcase.set('time', str(test_data['duration']))
                
                if test_data['status'] == 'failed':
                    failure = SubElement(testcase, 'failure')
                    failure.set('message', test_data['error'] or 'Test failed')
                    failure.text = test_data['error'] or 'No error details available'
                elif test_data['status'] == 'skipped':
                    SubElement(testcase, 'skipped')
        
        # Pretty print XML
        rough_string = tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        
        with open(output_path, 'w') as f:
            f.write(reparsed.toprettyxml(indent="  "))

async def main():
    """Main test runner function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run comprehensive tests for Lexicon enhanced features')
    parser.add_argument('--suite', help='Run specific test suite')
    parser.add_argument('--quick', action='store_true', help='Run only critical tests')
    parser.add_argument('--report', help='Generate report in specified format (json|html|junit)')
    parser.add_argument('--ci', action='store_true', help='CI mode - exit with non-zero on failures')
    
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner()
    
    if args.quick:
        # Only run critical tests
        runner.test_suites = [s for s in runner.test_suites if 'integration' in s.name.lower()]
    
    if args.suite:
        # Run specific suite
        runner.test_suites = [s for s in runner.test_suites if args.suite.lower() in s.name.lower()]
    
    results = await runner.run_all_tests()
    
    # Exit with appropriate code for CI
    if args.ci:
        if results['summary']['failed_suites'] > 0 or results['summary']['failed_tests'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
