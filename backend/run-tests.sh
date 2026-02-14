#!/bin/bash
# Smart test runner for avatar creation (System 1) and content generation (System 2) tests

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "=========================================="
echo "🧪 VixenBliss System 1 & 2 Testing Suite"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Parse arguments
SYSTEM=${1:-"all"}  # all, system1, system2, mock, smoke, contracts

cd "$BACKEND_DIR"

case $SYSTEM in
  system1)
    echo -e "${YELLOW}[SYSTEM 1] Avatar Creation Tests${NC}"
    echo -e "${YELLOW}Running MOCK tests (fast, no real APIs)...${NC}"
    python -m pytest tests/test_avatar_creation_mock.py tests/test_avatar_creation_smoke.py -v --tb=short
    ;;

  system2)
    echo -e "${YELLOW}[SYSTEM 2] Content Generation Tests${NC}"
    echo -e "${YELLOW}Running MOCK tests (fast, no real APIs)...${NC}"
    python -m pytest tests/test_content_generation_mock.py -v --tb=short
    echo -e "${GREEN}✅ System 2 mock tests passed${NC}"
    echo ""
    
    if [ "$RUN_PRODUCTION_TESTS" == "true" ]; then
      echo -e "${YELLOW}Running SMOKE tests (real APIs)...${NC}"
      python -m pytest tests/test_content_generation_smoke.py -m smoke -v --tb=short
      echo -e "${GREEN}✅ System 2 smoke tests passed${NC}"
    else
      echo -e "${YELLOW}⚠️  Skipping System 2 smoke tests. Run with: RUN_PRODUCTION_TESTS=true ./run-tests.sh system2${NC}"
    fi
    ;;

  mock)
    echo -e "${YELLOW}[MOCK] Running ALL MOCK tests (fast, no real APIs)...${NC}"
    python -m pytest tests/test_avatar_creation_mock.py tests/test_content_generation_mock.py -v --tb=short
    echo -e "${GREEN}✅ All mock tests passed${NC}"
    ;;

  smoke)
    echo -e "${YELLOW}[SMOKE] Running ALL SMOKE tests (real APIs)...${NC}"
    if [ "$RUN_PRODUCTION_TESTS" != "true" ]; then
      echo -e "${YELLOW}ℹ️  Set RUN_PRODUCTION_TESTS=true to enable${NC}"
      export RUN_PRODUCTION_TESTS=true
    fi
    python -m pytest tests/test_avatar_creation_smoke.py tests/test_content_generation_smoke.py -m smoke -v --tb=short
    echo -e "${GREEN}✅ All smoke tests passed${NC}"
    ;;

  all)
    echo -e "${YELLOW}[ALL] Running COMPLETE test suite (System 1 + System 2)...${NC}"
    echo ""
    echo -e "${YELLOW}Step 1: System 1 & 2 Mock tests (fast)...${NC}"
    python -m pytest tests/test_avatar_creation_mock.py tests/test_content_generation_mock.py -v --tb=short
    echo -e "${GREEN}✅ Step 1 passed${NC}"
    echo ""
    
    if [ "$RUN_PRODUCTION_TESTS" == "true" ]; then
      echo -e "${YELLOW}Step 2: System 1 & 2 Smoke tests (real APIs)...${NC}"
      python -m pytest tests/test_avatar_creation_smoke.py tests/test_content_generation_smoke.py -m smoke -v --tb=short
      echo -e "${GREEN}✅ Step 2 passed${NC}"
    else
      echo -e "${YELLOW}⚠️  Skipping smoke tests. Run with: RUN_PRODUCTION_TESTS=true ./run-tests.sh all${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}Step 3: Contract compliance...${NC}"
    python -m pytest tests/test_api_contracts.py -v --tb=short
    echo -e "${GREEN}✅ Step 3 passed${NC}"
    ;;

  contracts)
    echo -e "${YELLOW}Running contract compliance tests...${NC}"
    python -m pytest tests/test_api_contracts.py -v --tb=short
    echo -e "${GREEN}✅ Contract tests passed${NC}"
    ;;

  *)
    echo -e "${RED}Unknown test type: $SYSTEM${NC}"
    echo "Usage: $0 [all|system1|system2|mock|smoke|contracts]"
    echo ""
    echo "  all       - Run complete test suite (mock + smoke + contracts)"
    echo "  system1   - Avatar creation tests (System 1)"
    echo "  system2   - Content generation tests (System 2)"
    echo "  mock      - All mock tests (fast, no APIs)"
    echo "  smoke     - All smoke tests (real APIs, requires RUN_PRODUCTION_TESTS=true)"
    echo "  contracts - API contract compliance tests only"
    echo ""
    echo "Examples:"
    echo "  $0 system2              # Test Content Generation"
    echo "  RUN_PRODUCTION_TESTS=true $0 all  # Full suite with real APIs"
    ;;
esac

echo ""
echo "=========================================="
echo -e "${GREEN}✅ All tests completed!${NC}"
echo "=========================================="
