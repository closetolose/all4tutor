#!/usr/bin/env bash
# analyze-repo.sh — Detect AWS IaC type(s) in a repository
#
# Usage: bash analyze-repo.sh <repo-path>
#
# Output: Structured summary of detected IaC types, files, and AWS resources.

set -euo pipefail

REPO_PATH="${1:?Usage: analyze-repo.sh <repo-path>}"

if [[ ! -d "$REPO_PATH" ]]; then
  echo "ERROR: Directory not found: $REPO_PATH"
  exit 1
fi

echo "=========================================="
echo " AWS IaC Repository Analysis"
echo "=========================================="
echo "Repository: $REPO_PATH"
echo "Date:       $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo ""

# -------------------------------------------------------------------
# CloudFormation Detection
# -------------------------------------------------------------------
echo "--- CloudFormation Detection ---"
CFN_FILES=()

# Search YAML/JSON for AWSTemplateFormatVersion or CloudFormation resource types
while IFS= read -r -d '' file; do
  if grep -qlE '(AWSTemplateFormatVersion|AWS::CloudFormation|Type:\s*AWS::)' "$file" 2>/dev/null; then
    CFN_FILES+=("$file")
  fi
done < <(find "$REPO_PATH" -type f \( -name '*.yaml' -o -name '*.yml' -o -name '*.json' \) \
  ! -path '*/node_modules/*' ! -path '*/.terraform/*' ! -path '*/cdk.out/*' \
  ! -path '*/.git/*' -print0 2>/dev/null)

if [[ ${#CFN_FILES[@]} -gt 0 ]]; then
  echo "DETECTED: CloudFormation (${#CFN_FILES[@]} file(s))"
  for f in "${CFN_FILES[@]}"; do
    echo "  - ${f#$REPO_PATH/}"
  done

  # Count AWS resource types
  echo ""
  echo "  AWS Resources found:"
  for f in "${CFN_FILES[@]}"; do
    grep -oP 'Type:\s*\KAWS::[A-Za-z0-9]+::[A-Za-z0-9]+' "$f" 2>/dev/null
  done | sort | uniq -c | sort -rn | head -30 | while read -r count rtype; do
    echo "    $count x $rtype"
  done
else
  echo "NOT DETECTED"
fi

# Check for SAM
SAM_CONFIG=$(find "$REPO_PATH" -maxdepth 2 -name 'samconfig.toml' -o -name 'samconfig.yaml' 2>/dev/null | head -1)
if [[ -n "$SAM_CONFIG" ]]; then
  echo ""
  echo "  Note: SAM configuration detected ($SAM_CONFIG) — this is CloudFormation-based."
fi

echo ""

# -------------------------------------------------------------------
# CDK Detection
# -------------------------------------------------------------------
echo "--- CDK Detection ---"
CDK_JSON=$(find "$REPO_PATH" -maxdepth 3 -name 'cdk.json' ! -path '*/node_modules/*' 2>/dev/null | head -1)

if [[ -n "$CDK_JSON" ]]; then
  CDK_ROOT=$(dirname "$CDK_JSON")
  echo "DETECTED: CDK (cdk.json at ${CDK_JSON#$REPO_PATH/})"

  # Detect language
  CDK_LANG="unknown"
  if find "$CDK_ROOT" -name '*.ts' ! -path '*/node_modules/*' | head -1 | grep -q .; then
    if grep -rql 'aws-cdk-lib\|@aws-cdk/' "$CDK_ROOT" --include='*.ts' 2>/dev/null; then
      CDK_LANG="TypeScript"
    fi
  fi
  if find "$CDK_ROOT" -name '*.py' | head -1 | grep -q .; then
    if grep -rql 'aws_cdk\|from constructs' "$CDK_ROOT" --include='*.py' 2>/dev/null; then
      CDK_LANG="Python"
    fi
  fi
  echo "  Language: $CDK_LANG"

  # List stack files
  echo "  Stack files:"
  if [[ "$CDK_LANG" == "TypeScript" ]]; then
    find "$CDK_ROOT" -name '*.ts' ! -path '*/node_modules/*' ! -path '*/cdk.out/*' \
      -exec grep -l 'extends.*Stack\|new.*Stack' {} \; 2>/dev/null | while read -r f; do
      echo "    - ${f#$REPO_PATH/}"
    done
  elif [[ "$CDK_LANG" == "Python" ]]; then
    find "$CDK_ROOT" -name '*.py' \
      -exec grep -l 'Stack)\|class.*Stack' {} \; 2>/dev/null | while read -r f; do
      echo "    - ${f#$REPO_PATH/}"
    done
  fi

  # Check for synthesized output
  if [[ -d "$CDK_ROOT/cdk.out" ]]; then
    echo "  Synthesized output: cdk.out/ exists"
  fi
else
  echo "NOT DETECTED"
fi

echo ""

# -------------------------------------------------------------------
# Terraform Detection
# -------------------------------------------------------------------
echo "--- Terraform Detection ---"
TF_FILES=()

while IFS= read -r -d '' file; do
  TF_FILES+=("$file")
done < <(find "$REPO_PATH" -type f -name '*.tf' \
  ! -path '*/node_modules/*' ! -path '*/.terraform/*' ! -path '*/.git/*' \
  -print0 2>/dev/null)

if [[ ${#TF_FILES[@]} -gt 0 ]]; then
  echo "DETECTED: Terraform (${#TF_FILES[@]} .tf file(s))"

  # Group by directory (Terraform root modules)
  echo ""
  echo "  Root modules:"
  for f in "${TF_FILES[@]}"; do
    dirname "$f"
  done | sort -u | while read -r dir; do
    tf_count=$(find "$dir" -maxdepth 1 -name '*.tf' | wc -l)
    echo "    - ${dir#$REPO_PATH/} ($tf_count files)"
  done

  # Count AWS resource types
  echo ""
  echo "  AWS Resources found:"
  for f in "${TF_FILES[@]}"; do
    grep -oP 'resource\s+"(aws_[a-z0-9_]+)"' "$f" 2>/dev/null | grep -oP '"aws_[a-z0-9_]+"' | tr -d '"'
  done | sort | uniq -c | sort -rn | head -30 | while read -r count rtype; do
    echo "    $count x $rtype"
  done

  # Check for modules
  echo ""
  echo "  Module usage:"
  for f in "${TF_FILES[@]}"; do
    grep -oP 'source\s*=\s*"\K[^"]+' "$f" 2>/dev/null
  done | sort -u | while read -r mod; do
    echo "    - $mod"
  done

  # Check for state/lock
  LOCK_FILE=$(find "$REPO_PATH" -name '.terraform.lock.hcl' ! -path '*/.git/*' 2>/dev/null | head -1)
  if [[ -n "$LOCK_FILE" ]]; then
    echo ""
    echo "  Lock file: ${LOCK_FILE#$REPO_PATH/}"
  fi
else
  echo "NOT DETECTED"
fi

echo ""

# -------------------------------------------------------------------
# Summary
# -------------------------------------------------------------------
echo "=========================================="
echo " Summary"
echo "=========================================="

DETECTED=()
[[ ${#CFN_FILES[@]} -gt 0 ]] && DETECTED+=("CloudFormation")
[[ -n "${CDK_JSON:-}" ]] && DETECTED+=("CDK ($CDK_LANG)")
[[ ${#TF_FILES[@]} -gt 0 ]] && DETECTED+=("Terraform")

if [[ ${#DETECTED[@]} -eq 0 ]]; then
  echo "No AWS IaC code detected in this repository."
  echo ""
  echo "Possible reasons:"
  echo "  - The repository does not contain AWS infrastructure code"
  echo "  - IaC files are in a non-standard location or format"
  echo "  - The code uses a framework not covered by this analysis"
  exit 1
elif [[ ${#DETECTED[@]} -eq 1 ]]; then
  echo "Single IaC type detected: ${DETECTED[0]}"
else
  echo "Multiple IaC types detected:"
  for d in "${DETECTED[@]}"; do
    echo "  - $d"
  done
fi

echo ""
echo "Analysis complete."
