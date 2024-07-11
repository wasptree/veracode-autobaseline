<!-- ABOUT THE PROJECT -->
## About This Project


veracode-autobaseline is a Github action to automate the use of baseline files for the Veracode Pipeline Scan. 

The script will store and retrieve the baseline files in a central repository, removing the need to commit them into the application respository.

The baseline file will suppress unecessary flaw results from the Veracode Pipeline Scan (SAST)

Please see [**wasptree/veracode-autobaseline-pipeline**](https://github.com/Wasptree/veracode-autobaseline-pipeline) for the composite action, that will perform the pipeline scan and the autobaseline steps.

<!-- How it works -->
## How it works

The script will check if the action is running in a pull request event. If so, the script will check if a baseline file exists for the base branch (target branch). It will pull the baseline file and perform the pipeline scan.

On a merge event, when the Policy scan is performed, the **update** parameter can be used to store an updated baseline file in the baseline repository.

<!-- PARAMETERS -->
## Parameters

The composite function also supports all of the pipeline scan action parameters as well as those below ( https://github.com/veracode/Veracode-pipeline-scan-action )

| Input           | Description                                                                                   | Required |
|-----------------|-----------------------------------------------------------------------------------------------|----------|
| baseline_token  | Github Access Token                                                                           | true     |
| source          | Name of the repository where the baseline will be stored. - Default `<owner>/veracode-baseline` | false    |
| result_file     | Specify the name of the results/baseline file (json) to read in - Default `results.json`        | false    |
| commit          | Custom commit message                                                                         | false    |
| branch          | Override the default ref, which is the branch name                                            | false    |
| repo            | Override the default repository - Default is `$GITHUB_REPOSITORY`                              | false    |
| checkbf         | Check if the baseline file to be pushed is new (less than 10 minutes old) - Default `True`     | false    |
| update          | Whether a new baseline file should be pushed up to the repository - Default `False`            | false    |


<!-- SETUP -->
## Setup

1. Create baseline repsitory
   

A centralised repository in GitHub must be first created to store all the baseline files.

**This repository should be kept private as it will contain sensitive information**

By default the centralised repository is named **<org_name>/veracode-baseline**

2. Generate private access token

Once created , an access token is generated so that the script can read/write baselines from this repository.

<!-- USAGE EXAMPLES -->
## Usage Examples

A pipeline scan & autobaseline composite action is available at Wasptree/veracode-autobaseline-pipeline

Pipeline scan / Run on pull request : 

```
        - name: pipeline-scan action step
          id: pipeline-scan
          uses: wasptree/veracode-autobaseline-pipeline@v0.1
          with:
            vid: ${{ secrets.VID }}
            vkey: ${{ secrets.VKEY }}
            file: "./target/verademo.war"
            baseline_file: ".veracode-autobaseline/baseline.json"
            baseline_token: ${{ secrets.TOKEN }}
```

The following example will perform the Policy scan and the pipelinescan baseline update in parallel

```
jobs:
  policy-scan:
      name: Veracode Policy Scan
      runs-on: ubuntu-latest

      steps:
        - name: checkout repo
          uses: actions/checkout@v2
          
        - name: Veracode Upload And Scan
          uses: veracode/veracode-uploadandscan-action@0.2.7
          with:
            appname: 'verademo_github'
            createprofile: false
            filepath: 'target/verademo.war'
            vid: '${{secrets.VID}}'
            vkey: '${{secrets.VKEY}}'
            deleteincompletescan: 2

  update-baseline:
      name: Update Baseline
      runs-on: ubuntu-latest

      steps:
        - name: checkout repo
          uses: actions/checkout@v2
        
        # run the pipeline scan action
        - name: pipeline-scan action step
          id: pipeline-scan
          uses: wasptree/veracode-autobaseline-pipeline@master
          with:
            vid: ${{ secrets.VID }}
            vkey: ${{ secrets.VKEY }}
            file: "./target/verademo.war"
            baseline_file: ".veracode-autobaseline/baseline.json"
            baseline_token: ${{ secrets.TOKEN }}
            update: true
```

<!-- To Do -->
## To Do

1. Add full examples 
2. Add example using the Veracode Github app
3. Add platform checks to validate baseline file matches existing policy scan results
