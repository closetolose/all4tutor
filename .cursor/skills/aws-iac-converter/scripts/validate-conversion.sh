#!/usr/bin/env bash
# validate-conversion.sh — Validate converted IaC code
#
# Usage: bash validate-conversion.sh <target-path> <target-type>
#
#   target-type: cloudformation | terraform | cdk-typescript | cdk-python
#
# Runs syntax validation, formatting, and linting for the target IaC type.
# Linting errors and validation failures should be resolved.
# Security-specific scans (e.g. Checkov, cfn-guard) are report-only — do not
# resolve (findings may be intentional from the source).

set -euo pipefail

TARGET_PATH="${1:?Usage: validate-conversion.sh <target-path> <target-type>}"
TARGET_TYPE="${2:?Usage: validate-conversion.sh <target-path> <target-type>}"

if [[ ! -d "$TARGET_PATH" ]]; then
  echo "ERROR: Directory not found: $TARGET_PATH"
  exit 1
fi

PASS=0
FAIL=0
WARN=0
REPORT=0

report() {
  local status="$1" check="$2" detail="$3"
  case "$status" in
    PASS)  ((PASS++))  ; echo "[PASS] $check" ;;
    FAIL)  ((FAIL++))  ; echo "[FAIL] $check — $detail" ;;
    WARN)  ((WARN++))  ; echo "[WARN] $check — $detail" ;;
    SKIP) echo "[SKIP] $check — $detail" ;;
    REPORT) ((REPORT++)); echo "[REPORT] $check — $detail (report only)" ;;
  esac
}

echo "=========================================="
echo " IaC Conversion Validation"
echo "=========================================="
echo "Target path: $TARGET_PATH"
echo "Target type: $TARGET_TYPE"
echo "Date:        $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo ""

# -------------------------------------------------------------------
# CloudFormation Validation
# -------------------------------------------------------------------
if [[ "$TARGET_TYPE" == "cloudformation" ]]; then
  echo "--- CloudFormation Validation ---"
  echo ""

  # Find template files
  TEMPLATES=()
  while IFS= read -r -d '' f; do
    if grep -qlE '(AWSTemplateFormatVersion|Type:\s*AWS::)' "$f" 2>/dev/null; then
      TEMPLATES+=("$f")
    fi
  done < <(find "$TARGET_PATH" -type f \( -name '*.yaml' -o -name '*.yml' -o -name '*.json' \) -print0 2>/dev/null)

  if [[ ${#TEMPLATES[@]} -eq 0 ]]; then
    report FAIL "Template detection" "No CloudFormation templates found"
  else
    report PASS "Template detection" "${#TEMPLATES[@]} template(s) found"

    for tmpl in "${TEMPLATES[@]}"; do
      rel="${tmpl#$TARGET_PATH/}"

      # YAML/JSON syntax check
      if command -v python3 &>/dev/null; then
        if [[ "$tmpl" == *.json ]]; then
          if python3 -c "import json; json.load(open('$tmpl'))" 2>/dev/null; then
            report PASS "JSON syntax ($rel)" ""
          else
            report FAIL "JSON syntax ($rel)" "Invalid JSON"
          fi
        else
          if python3 -c "import yaml; yaml.safe_load(open('$tmpl'))" 2>/dev/null; then
            report PASS "YAML syntax ($rel)" ""
          else
            report FAIL "YAML syntax ($rel)" "Invalid YAML"
          fi
        fi
      else
        report SKIP "Syntax check ($rel)" "python3 not available"
      fi

      # AWS CLI validation
      if command -v aws &>/dev/null; then
        if aws cloudformation validate-template --template-body "file://$tmpl" &>/dev/null; then
          report PASS "AWS CFN validate ($rel)" ""
        else
          report FAIL "AWS CFN validate ($rel)" "Template validation failed"
        fi
      else
        report SKIP "AWS CFN validate ($rel)" "aws CLI not available"
      fi
    done
  fi

  # cfn-lint — linting/validation; resolve errors and warnings
  if command -v cfn-lint &>/dev/null; then
    echo ""
    echo "Running cfn-lint..."
    for tmpl in "${TEMPLATES[@]}"; do
      rel="${tmpl#$TARGET_PATH/}"
      lint_output=$(cfn-lint "$tmpl" 2>&1) || true
      if [[ -z "$lint_output" ]]; then
        report PASS "cfn-lint ($rel)" ""
      else
        error_count=$(echo "$lint_output" | grep -c '^E' || true)
        warn_count=$(echo "$lint_output" | grep -c '^W' || true)
        if [[ "$error_count" -gt 0 ]]; then
          report FAIL "cfn-lint ($rel)" "$error_count error(s), $warn_count warning(s)"
        else
          report WARN "cfn-lint ($rel)" "$warn_count warning(s)"
        fi
      fi
    done
  else
    report SKIP "cfn-lint" "cfn-lint not installed (pip install cfn-lint)"
  fi
fi

# -------------------------------------------------------------------
# Terraform Validation
# -------------------------------------------------------------------
if [[ "$TARGET_TYPE" == "terraform" ]]; then
  echo "--- Terraform Validation ---"
  echo ""

  # Check for .tf files
  TF_COUNT=$(find "$TARGET_PATH" -name '*.tf' | wc -l)
  if [[ "$TF_COUNT" -eq 0 ]]; then
    report FAIL "File detection" "No .tf files found"
  else
    report PASS "File detection" "$TF_COUNT .tf file(s) found"
  fi

  # terraform fmt check
  if command -v terraform &>/dev/null; then
    fmt_output=$(terraform fmt -check -recursive "$TARGET_PATH" 2>&1) || true
    if [[ -z "$fmt_output" ]]; then
      report PASS "terraform fmt" ""
    else
      unformatted=$(echo "$fmt_output" | wc -l)
      report WARN "terraform fmt" "$unformatted file(s) need formatting"
      echo "  Run: terraform fmt -recursive $TARGET_PATH"
    fi

    # terraform init (required before validate)
    echo ""
    echo "Running terraform init..."
    if terraform -chdir="$TARGET_PATH" init -backend=false -input=false &>/dev/null; then
      report PASS "terraform init" ""

      # terraform validate
      echo "Running terraform validate..."
      validate_output=$(terraform -chdir="$TARGET_PATH" validate -json 2>&1) || true
      if echo "$validate_output" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('valid') else 1)" 2>/dev/null; then
        report PASS "terraform validate" ""
      else
        error_count=$(echo "$validate_output" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error_count',0))" 2>/dev/null || echo "?")
        report FAIL "terraform validate" "$error_count error(s)"
      fi
    else
      report FAIL "terraform init" "Init failed — check provider configuration"
    fi
  else
    report SKIP "terraform validate" "terraform CLI not installed"
  fi

  # Checkov scan — report only (see skill verification policy)
  if command -v checkov &>/dev/null; then
    echo ""
    echo "Running Checkov security scan (report only)..."
    checkov_output=$(checkov -d "$TARGET_PATH" --framework terraform --compact --quiet 2>&1) || true
    passed=$(echo "$checkov_output" | grep -oP 'Passed checks: \K\d+' || echo "0")
    failed=$(echo "$checkov_output" | grep -oP 'Failed checks: \K\d+' || echo "0")
    if [[ "$failed" -eq 0 ]]; then
      report PASS "Checkov scan" "$passed check(s) passed"
    else
      report REPORT "Checkov scan" "$passed passed, $failed failed"
    fi
  else
    report SKIP "Checkov scan" "checkov not installed (pip install checkov)"
  fi
fi

# -------------------------------------------------------------------
# CDK TypeScript Validation
# -------------------------------------------------------------------
if [[ "$TARGET_TYPE" == "cdk-typescript" ]]; then
  echo "--- CDK (TypeScript) Validation ---"
  echo ""

  # Check for cdk.json
  if [[ -f "$TARGET_PATH/cdk.json" ]]; then
    report PASS "cdk.json" ""
  else
    report FAIL "cdk.json" "Missing cdk.json"
  fi

  # Check for package.json
  if [[ -f "$TARGET_PATH/package.json" ]]; then
    report PASS "package.json" ""
  else
    report FAIL "package.json" "Missing package.json"
  fi

  # npm install
  if command -v npm &>/dev/null && [[ -f "$TARGET_PATH/package.json" ]]; then
    echo "Running npm install..."
    if (cd "$TARGET_PATH" && npm install --quiet 2>&1) >/dev/null; then
      report PASS "npm install" ""

      # TypeScript build
      echo "Running build..."
      if (cd "$TARGET_PATH" && npm run build 2>&1) >/dev/null; then
        report PASS "TypeScript build" ""
      else
        report FAIL "TypeScript build" "Build failed — check for TypeScript errors"
      fi

      # cdk synth
      if command -v cdk &>/dev/null || command -v npx &>/dev/null; then
        echo "Running cdk synth..."
        CDK_CMD="npx cdk"
        if (cd "$TARGET_PATH" && $CDK_CMD synth --quiet 2>&1) >/dev/null; then
          report PASS "cdk synth" ""
        else
          report FAIL "cdk synth" "Synthesis failed"
        fi
      else
        report SKIP "cdk synth" "cdk CLI not available"
      fi
    else
      report FAIL "npm install" "Dependency installation failed"
    fi
  else
    report SKIP "npm install" "npm not available or package.json missing"
  fi
fi

# -------------------------------------------------------------------
# CDK Python Validation
# -------------------------------------------------------------------
if [[ "$TARGET_TYPE" == "cdk-python" ]]; then
  echo "--- CDK (Python) Validation ---"
  echo ""

  # Check for cdk.json
  if [[ -f "$TARGET_PATH/cdk.json" ]]; then
    report PASS "cdk.json" ""
  else
    report FAIL "cdk.json" "Missing cdk.json"
  fi

  # Check for requirements.txt
  if [[ -f "$TARGET_PATH/requirements.txt" ]]; then
    report PASS "requirements.txt" ""
  else
    report FAIL "requirements.txt" "Missing requirements.txt"
  fi

  # pip install
  if command -v pip &>/dev/null && [[ -f "$TARGET_PATH/requirements.txt" ]]; then
    echo "Installing Python dependencies..."
    if pip install -r "$TARGET_PATH/requirements.txt" --quiet 2>&1 >/dev/null; then
      report PASS "pip install" ""

      # cdk synth
      if command -v cdk &>/dev/null; then
        echo "Running cdk synth..."
        if (cd "$TARGET_PATH" && cdk synth --quiet 2>&1) >/dev/null; then
          report PASS "cdk synth" ""
        else
          report FAIL "cdk synth" "Synthesis failed"
        fi
      else
        report SKIP "cdk synth" "cdk CLI not available"
      fi
    else
      report FAIL "pip install" "Dependency installation failed"
    fi
  else
    report SKIP "pip install" "pip not available or requirements.txt missing"
  fi

  # Python syntax check
  if command -v python3 &>/dev/null; then
    echo "Checking Python syntax..."
    py_errors=0
    while IFS= read -r -d '' pyfile; do
      if ! python3 -m py_compile "$pyfile" 2>/dev/null; then
        ((py_errors++))
        report FAIL "Python syntax (${pyfile#$TARGET_PATH/})" "Syntax error"
      fi
    done < <(find "$TARGET_PATH" -name '*.py' ! -path '*/.venv/*' ! -path '*/venv/*' -print0 2>/dev/null)
    if [[ "$py_errors" -eq 0 ]]; then
      report PASS "Python syntax" "All files valid"
    fi
  fi
fi

# -------------------------------------------------------------------
# Results Summary
# -------------------------------------------------------------------
echo ""
echo "=========================================="
echo " Validation Summary"
echo "=========================================="
echo "  PASS:   $PASS"
echo "  FAIL:   $FAIL"
echo "  WARN:   $WARN"
echo "  REPORT: $REPORT (security — include in conversion report only)"
echo ""

if [[ "$FAIL" -gt 0 ]]; then
  echo "RESULT: VALIDATION FAILED — $FAIL issue(s) must be fixed"
  exit 1
elif [[ "$WARN" -gt 0 ]]; then
  echo "RESULT: VALIDATION PASSED WITH WARNINGS — $WARN item(s) to review"
  exit 0
else
  echo "RESULT: VALIDATION PASSED"
  exit 0
fi
