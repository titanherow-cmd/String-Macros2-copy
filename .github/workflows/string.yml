name: String macros (with combination file in zip)

on:
  workflow_dispatch:
    inputs:
      enable_chat:
        description: 'Enable chat inserts (50% of files)'
        required: false
        default: false
        type: boolean
      
      use_specific_folders:
        description: 'Use specific folders only (filter mode)'
        required: false
        default: false
        type: boolean
      
      versions:
        description: 'Total versions to generate'
        required: true
        default: '12'
      
      target_minutes:
        description: 'Target duration per stringed file'
        required: true
        default: '35'
      
      specific_folders:
        description: 'Specific folders to include (one per line, leave empty to use saved list)'
        required: false
        default: ''
        type: string

permissions:
  contents: write

jobs:
  string:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          
      - name: Get current BUNDLE_SEQ
        id: seq
        run: |
          if [ -f .github/string_bundle_counter.txt ]; then
            VAL=$(cat .github/string_bundle_counter.txt)
          else
            VAL=1
          fi
          echo "BUNDLE_SEQ=$VAL" >> "$GITHUB_ENV"
      
      - name: Setup specific folders list
        run: |
          # Check if user provided folder names in the UI
          if [ -n "${{ github.event.inputs.specific_folders }}" ]; then
            echo "📝 Using specific folders from UI input"
            echo "${{ github.event.inputs.specific_folders }}" > .github/specific_folders_temp.txt
            FOLDERS_FILE=".github/specific_folders_temp.txt"
          elif [ -f .github/specific_folders_to_include.txt ]; then
            echo "📁 Using saved folder list from .github/specific_folders_to_include.txt"
            FOLDERS_FILE=".github/specific_folders_to_include.txt"
          else
            echo "🌐 No specific folders file found"
            FOLDERS_FILE=""
          fi
          echo "FOLDERS_FILE=$FOLDERS_FILE" >> "$GITHUB_ENV"
        
      - name: Execute string macro script
        run: |
          mkdir -p output
          
          CMD="python3 string_macros.py input_macros output"
          CMD="$CMD --versions ${{ github.event.inputs.versions }}"
          CMD="$CMD --target-minutes ${{ github.event.inputs.target_minutes }}"
          CMD="$CMD --bundle-id ${{ env.BUNDLE_SEQ }}"
          
          # Chat inserts toggle
          if [ "${{ inputs.enable_chat }}" = "false" ]; then
            CMD="$CMD --no-chat"
            echo "🔕 Chat inserts DISABLED"
          else
            echo "✅ Chat inserts ENABLED (50% of files)"
          fi
          
          # Specific folders toggle + file
          if [ "${{ inputs.use_specific_folders }}" = "true" ]; then
            if [ -n "$FOLDERS_FILE" ] && [ -f "$FOLDERS_FILE" ]; then
              echo "📋 Processing specific folders only:"
              cat "$FOLDERS_FILE"
              CMD="$CMD --specific-folders $FOLDERS_FILE"
            else
              echo "⚠️ Specific folders mode enabled but no folder list found!"
              echo "💡 Add folders to .github/specific_folders_to_include.txt or paste in UI field"
              echo "🌐 Will process ALL folders"
            fi
          else
            echo "🌐 Processing ALL folders"
          fi
          
          echo "Running: $CMD"
          $CMD
            
      - name: Commit and Push Counter Update
        run: |
          NEW_VAL=$((BUNDLE_SEQ + 1))
          mkdir -p .github
          echo "$NEW_VAL" > .github/string_bundle_counter.txt
          git config --global user.name 'github-actions[bot]'
          git config --global user.email 'github-actions[bot]@users.noreply.github.com'
          git add .github/string_bundle_counter.txt
          git commit -m "Increment string bundle counter to $NEW_VAL" || echo "No changes"
          git push || echo "Push failed"
            
      - name: Create ZIP artifact
        run: |
          BUNDLE_NAME="stringed_bundle_${{ env.BUNDLE_SEQ }}"
          ZIP_FILE="stringed_macros_${{ env.BUNDLE_SEQ }}.zip"
          
          ls -R output/
          
          if [ -d "output/$BUNDLE_NAME" ]; then
            cd output && zip -r "../$ZIP_FILE" "$BUNDLE_NAME" COMBINATION_HISTORY_*.txt
          else
            echo "Error: Directory output/$BUNDLE_NAME was not found!"
            exit 1
          fi
          echo "FINAL_ZIP=$ZIP_FILE" >> "$GITHUB_ENV"
          
      - name: Upload stringed ZIP artifact
        uses: actions/upload-artifact@v4
        with:
          name: stringed_macros_bundle_${{ env.BUNDLE_SEQ }}
          path: ${{ env.FINAL_ZIP }}
