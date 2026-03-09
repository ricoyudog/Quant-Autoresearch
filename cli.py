#!/usr/bin/env python3
"""
Enhanced CLI for Quant Autoresearch with OPENDEV integration
"""
import argparse
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from core.engine import QuantAutoresearchEngine
from utils.iteration_tracker import iteration_tracker
from context.compactor import ContextCompactor
from safety.guard import SafetyGuard, SafetyLevel, ApprovalMode
from memory.playbook import Playbook
from models.router import model_router

def run_engine(args):
    """Run the Quant Autoresearch engine with OPENDEV features"""
    print(f"🚀 Starting Quant Autoresearch Engine (OPENDEV)")
    print(f"📊 Safety Level: {args.safety_level}")
    print(f"🧠 Max Context: {args.max_context}%")
    print(f"🔄 Max Iterations: {args.iterations}")
    print(f"⏱️  Duration: {args.duration} minutes" if args.duration else "")
    print(f"🤖 Thinking Model: {args.thinking_model}")
    print(f"🤖 Reasoning Model: {args.reasoning_model}")
    print(f"🔧 Lazy Tools: {args.lazy_tools}")
    print(f"✅ Approval Mode: {args.approval_mode}")
    print("-" * 60)
    
    # Initialize engine with OPENDEV configuration
    engine = QuantAutoresearchEngine(
        safety_level=SafetyLevel(args.safety_level.lower()),
        max_context_percent=args.max_context,
        thinking_model=args.thinking_model,
        reasoning_model=args.reasoning_model,
        lazy_tools=args.lazy_tools,
        approval_mode=ApprovalMode(args.approval_mode.lower())
    )
    
    # Run the engine
    try:
        engine.run(max_iterations=args.iterations)
        
        # Show final statistics
        print("\n" + "=" * 60)
        print("📈 OPENDEV SESSION SUMMARY")
        print("=" * 60)
        
        # Engine statistics
        context_status = engine.compactor.get_context_status()
        safety_summary = engine.safety_guard.get_safety_summary()
        
        print(f"✅ Iterations Completed: {engine.iteration_count}")
        print(f"🧠 Context Usage: {context_status['usage_percent']:.1f}%")
        print(f"🛡️  Safety Validations: {safety_summary.get('approved_operations_count', 0)}")
        print(f"🚫 Blocked Operations: {safety_summary['blocked_operations']}")
        
        # Model router statistics
        model_stats = model_router.get_usage_stats()
        print(f"🤖 Model Usage:")
        print(f"   - Thinking calls: {model_stats['calls']['thinking_calls']}")
        print(f"   - Reasoning calls: {model_stats['calls']['reasoning_calls']}")
        print(f"   - Total cost: ${model_stats['total_cost']:.4f}")
        
        # Iteration tracking
        session_stats = iteration_tracker.get_session_stats()
        if session_stats.get("total_iterations", 0) > 0:
            print(f"📊 Success Rate: {session_stats['success_rate']:.1%}")
            print(f"💯 Best Score: {session_stats['best_score']:.3f}")
            print(f"⏱️  Session Duration: {session_stats['session_duration_minutes']:.1f} minutes")
        
        # Playbook statistics
        if args.lazy_tools:
            playbook_stats = engine.playbook.get_playbook_statistics()
            print(f"📚 Playbook:")
            print(f"   - Patterns stored: {playbook_stats['total_patterns']}")
            print(f"   - Avg success rate: {playbook_stats['average_success_rate']:.2%}")
            print(f"   - Cache hit rate: {playbook_stats['cache_hit_rate']:.1%}")
        
        print("\n🎉 OPENDEV engine run completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Engine stopped by user")
    except Exception as e:
        print(f"\n❌ Engine error: {str(e)}")
        sys.exit(1)

def show_status(args):
    """Show current system status with OPENDEV components"""
    print("📊 Quant Autoresearch OPENDEV Status")
    print("=" * 50)
    
    # Context status
    compactor = ContextCompactor()
    context_status = compactor.get_context_status()
    print(f"🧠 Context Usage: {context_status['usage_percent']:.1f}%")
    print(f"📝 Context History: {len(context_status['context_history'])} operations")
    print(f"🗂️  Masked Outputs: {len(context_status['masked_outputs'])}")
    print(f"✂️  Pruned Operations: {len(context_status['pruned_operations'])}")
    print(f"📝 Summarizations: {len(context_status['summarized_contexts'])}")
    
    # Safety status
    guard = SafetyGuard()
    safety_summary = guard.get_safety_summary()
    print(f"🛡️  Safety Level: {safety_summary['safety_level']}")
    print(f"✅ Validations Passed: {safety_summary.get('approved_operations_count', 0)}")
    print(f"🚫 Operations Blocked: {safety_summary['blocked_operations']}")
    print(f"🪝 Hooks Triggered: {safety_summary['hooks_triggered']}")
    
    # Model router status
    model_stats = model_router.get_usage_stats()
    print(f"🤖 Model Router:")
    print(f"   - Total calls: {model_stats['calls']['thinking_calls'] + model_stats['calls']['reasoning_calls']}")
    print(f"   - Total cost: ${model_stats['total_cost']:.4f}")
    
    # Iteration status
    session_stats = iteration_tracker.get_session_stats()
    if "total_iterations" in session_stats and session_stats["total_iterations"] > 0:
        print(f"🔄 Total Iterations: {session_stats['total_iterations']}")
        print(f"📈 Success Rate: {session_stats['success_rate']:.1%}")
        print(f"💯 Best Score: {session_stats['best_score']:.3f}")
        print(f"⏱️  Session Duration: {session_stats['session_duration_minutes']:.1f} minutes")
    else:
        print("🔄 No iterations logged yet")
    
    # Playbook status
    playbook = Playbook()
    playbook_stats = playbook.get_playbook_statistics()
    print(f"📚 Playbook:")
    print(f"   - Total patterns: {playbook_stats['total_patterns']}")
    print(f"   - Cache size: {playbook_stats['cache_size']}")
    print(f"   - Recent queries: {playbook_stats['recent_queries']}")

def show_report(args):
    """Show detailed performance report with OPENDEV metrics"""
    print("📊 Quant Autoresearch OPENDEV Performance Report")
    print("=" * 60)
    
    # Session statistics
    session_stats = iteration_tracker.get_session_stats()
    if "total_iterations" in session_stats and session_stats["total_iterations"] > 0:
        print(f"📊 SESSION OVERVIEW")
        print(f"Total Iterations: {session_stats['total_iterations']}")
        print(f"Session Duration: {session_stats['session_duration_minutes']:.1f} minutes")
        print(f"Iterations per Hour: {session_stats['iterations_per_hour']:.1f}")
        print(f"Success Rate: {session_stats['success_rate']:.1%}")
        print(f"Crash Rate: {session_stats['crash_rate']:.1%}")
        print()
        
        print(f"📈 PERFORMANCE METRICS")
        print(f"Average Score: {session_stats['average_score']:.3f}")
        print(f"Best Score: {session_stats['best_score']:.3f}")
        print(f"Worst Score: {session_stats['worst_score']:.3f}")
        print()
        
        # Recent iterations
        recent_summary = iteration_tracker.get_iteration_summary(last_n=5)
        print(f"🔄 RECENT ITERATIONS (Last 5)")
        for i, iteration in enumerate(recent_summary.get("recent_iterations", []), 1):
            score = iteration.get("score", "N/A")
            status = iteration.get("status", "UNKNOWN")
            hypothesis = iteration.get("hypothesis", "No hypothesis")[:40] + "..."
            print(f"{i}. [{status}] Score: {score} - {hypothesis}")
        print()
        
        # Performance trend
        trend = iteration_tracker.get_performance_trend()
        if "trend" in trend:
            print(f"📊 PERFORMANCE TREND")
            print(f"Trend: {trend['trend'].title()}")
            print(f"Improvement: {trend['improvement']:+.3f}")
            print(f"Recent Average: {trend['recent_average']:.3f}")
        print()
        
        # Hypothesis analysis
        hypothesis_analysis = iteration_tracker.get_hypothesis_analysis()
        if "total_hypotheses" in hypothesis_analysis:
            print(f"💡 HYPOTHESIS ANALYSIS")
            print(f"Total Hypotheses: {hypothesis_analysis['total_hypotheses']}")
            print(f"Success Rate: {hypothesis_analysis['success_rate']:.1%}")
            
            if hypothesis_analysis.get("best_hypothesis"):
                best = hypothesis_analysis["best_hypothesis"]
                print(f"Best Hypothesis: {best['hypothesis'][:50]}... (Score: {best['score']:.3f})")
        print()
        
        # Stagnation detection
        stagnation = iteration_tracker.detect_stagnation()
        if stagnation.get("stagnating"):
            print(f"⚠️  STAGNATION DETECTED")
            print(f"Score Variance: {stagnation['score_variance']:.3f}")
            print(f"Recommendation: {stagnation['recommendation']}")
        else:
            print(f"✅ PERFORMANCE HEALTH")
            print(f"Score variance: {stagnation.get('score_variance', 'N/A')}")
            print("Performance is varying normally")
        print()
        
        # OPENDEV specific metrics
        print(f"🚀 OPENDEV SYSTEM METRICS")
        
        # Context management
        compactor = ContextCompactor()
        acc_stats = compactor.get_acc_statistics()
        print(f"🧠 Adaptive Context Compaction:")
        print(f"   - Current stage: {acc_stats['current_status']['acc_stage']}")
        print(f"   - Total masked: {acc_stats['total_masked']}")
        print(f"   - Total pruned: {acc_stats['total_pruned']}")
        print(f"   - Total summarized: {acc_stats['total_summarized']}")
        print(f"   - Compression ratio: {acc_stats['compression_ratio']:.2f}")
        print()
        
        # Safety system
        guard = SafetyGuard()
        safety_summary = guard.get_safety_summary()
        print(f"🛡️  Defense-in-Depth Safety:")
        print(f"   - Layers configured: {len(safety_summary['schema_gates'])}")
        print(f"   - Tools validated: {safety_summary['tool_validators']}")
        print(f"   - Approval required: {safety_summary['blocked_operations']}")
        print()
        
        # Model routing
        model_stats = model_router.get_usage_stats()
        print(f"🤖 Multi-Model Routing:")
        print(f"   - Thinking calls: {model_stats['calls']['thinking_calls']}")
        print(f"   - Reasoning calls: {model_stats['calls']['reasoning_calls']}")
        print(f"   - Summarization calls: {model_stats['calls']['summarization_calls']}")
        print(f"   - Total cost: ${model_stats['total_cost']:.4f}")
        print(f"   - Cost breakdown: {model_stats['cost_breakdown']}")
        print()
        
        # Playbook memory
        playbook = Playbook()
        playbook_stats = playbook.get_playbook_statistics()
        print(f"📚 Dual-Memory Playbook:")
        print(f"   - Patterns stored: {playbook_stats['total_patterns']}")
        print(f"   - Average success rate: {playbook_stats['average_success_rate']:.2%}")
        print(f"   - Total usage: {playbook_stats['total_usage']}")
        print(f"   - Cache hit rate: {playbook_stats['cache_hit_rate']:.1%}")
        print(f"   - Response time: {playbook_stats['avg_response_time_ms']:.1f}ms")
        
    else:
        print("📊 No data available. Run the engine first!")

def test_opendev(args):
    """Test OPENDEV components"""
    print("🧪 Testing OPENDEV Components")
    print("=" * 40)
    
    # Test model router
    print("1. Testing Multi-Model Router...")
    try:
        from models.router import model_router
        thinking_result = model_router.thinking_phase({
            "current_situation": "Test scenario",
            "current_goal": "Test goal"
        })
        print(f"   ✅ Thinking phase: {thinking_result['success']}")
        print(f"   🤖 Model used: {thinking_result.get('model_used', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Model router error: {e}")
    
    # Test 4-stage ACC
    print("\n2. Testing 4-Stage Adaptive Context Compaction...")
    try:
        from context.compactor import ContextCompactor
        compactor = ContextCompactor()
        
        # Simulate operations to trigger different stages
        for i in range(5):
            large_data = {"result": "x" * 500, "iteration": i}
            compaction = compactor.adaptive_context_compaction(f"test_operation_{i}", large_data)
        
        status = compactor.get_context_status()
        print(f"   ✅ ACC working: {status['acc_stage']}")
        print(f"   🧠 Usage: {status['usage_percent']:.1f}%")
    except Exception as e:
        print(f"   ❌ ACC error: {e}")
    
    # Test 5-layer safety
    print("\n3. Testing 5-Layer Defense-in-Depth Safety...")
    try:
        from safety.guard import SafetyGuard, SubagentType
        guard = SafetyGuard()
        
        operation = {
            "tool_name": "generate_strategy_code",
            "parameters": {"position_size": 0.3}
        }
        
        safety_result = guard.defense_in_depth_check(operation, SubagentType.EXECUTOR)
        print(f"   ✅ Safety check: {safety_result['safe']}")
        print(f"   🛡️  Layers passed: {len(safety_result['layers_passed'])}")
    except Exception as e:
        print(f"   ❌ Safety system error: {e}")
    
    # Test lazy tool discovery
    print("\n4. Testing Lazy Tool Discovery...")
    try:
        from tools.registry import LazyToolRegistry, SubagentType
        registry = LazyToolRegistry()
        
        search_result = registry.search_tools("research", SubagentType.PLANNER)
        print(f"   ✅ Tool search: {search_result['total_matches']} tools found")
        
        schema = registry.load_tool_schema("search_research", SubagentType.PLANNER)
        print(f"   🔧 Schema loaded: {schema.get('name', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Tool registry error: {e}")
    
    # Test playbook memory
    print("\n5. Testing SQLite Playbook...")
    try:
        from memory.playbook import Playbook
        playbook = Playbook()
        
        # Store a test pattern
        pattern_hash = playbook.store_pattern(
            "Test hypothesis",
            "test strategy code",
            {"sharpe_ratio": 1.2, "max_drawdown": 0.15}
        )
        
        stats = playbook.get_playbook_statistics()
        print(f"   ✅ Playbook working: {stats['total_patterns']} patterns")
        print(f"   📚 Pattern stored: {pattern_hash[:8] if pattern_hash else 'None'}")
    except Exception as e:
        print(f"   ❌ Playbook error: {e}")
    
    print("\n🎉 OPENDEV component testing completed!")

def main():
    """Main CLI entry point with OPENDEV features"""
    parser = argparse.ArgumentParser(
        description="Quant Autoresearch - Autonomous Trading Strategy Research (OPENDEV)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
OPENDEV Examples:
  %(prog)s run --iterations 10                                    # Basic run
  %(prog)s run --iterations 10 --safety-level HIGH --lazy-tools  # OPENDEV run
  %(prog)s run --thinking-model llama-3.1-8b-instant             # Custom models
  %(prog)s status                                                  # Show OPENDEV status
  %(prog)s report                                                  # Detailed OPENDEV report
  %(prog)s test                                                    # Test OPENDEV components
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run command with OPENDEV flags
    run_parser = subparsers.add_parser("run", help="Run the OPENDEV research engine")
    run_parser.add_argument("--iterations", type=int, default=10, 
                           help="Maximum number of iterations (default: 10)")
    run_parser.add_argument("--safety-level", type=str, default="high", 
                           choices=["low", "medium", "high", "critical"], 
                           help="Safety level (default: high)")
    run_parser.add_argument("--max-context", type=int, default=95, 
                           help="Maximum context percentage (default: 95)")
    run_parser.add_argument("--duration", type=int, 
                           help="Maximum duration in minutes")
    run_parser.add_argument("--thinking-model", type=str, default="llama-3.1-8b-instant",
                           help="Thinking phase model (default: llama-3.1-8b-instant)")
    run_parser.add_argument("--reasoning-model", type=str, default="llama-3.3-70b-versatile",
                           help="Reasoning phase model (default: llama-3.3-70b-versatile)")
    run_parser.add_argument("--lazy-tools", action="store_true", default=True,
                           help="Enable lazy tool discovery (default: True)")
    run_parser.add_argument("--approval-mode", type=str, default="semi",
                           choices=["auto", "semi", "manual"],
                           help="Runtime approval mode (default: semi)")
    run_parser.set_defaults(func=run_engine)
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show OPENDEV system status")
    status_parser.set_defaults(func=show_status)
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Show detailed OPENDEV performance report")
    report_parser.set_defaults(func=show_report)
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test OPENDEV components")
    test_parser.set_defaults(func=test_opendev)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    args.func(args)

if __name__ == "__main__":
    main()
