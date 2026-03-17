# SOLVE-IT extensions (SOLVE-IT-X)

The repository provides everything you need to start building with SOLVE-IT-X (extensions to the SOLVE-IT knowledge base)

# Contents of this repository

* An example extension: when combined with the base SOLVE-IT repository data, this demonstrates how to add additional content to techniques, weaknesses and mitigations using the KB API and extension data.

* This example can be built with the helper script `build_solve-it-x.py` in the root of the project. This will:
  - clone the main SOLVE-IT repo into a new folder `solve-it-clone`
  - install any required dependencies from the cloned repo
  - copy over the demo extension into the cloned repo
  - copy over the pre-written extension_config.json file (and any custom global config)
  - run the HTML report generation script from the cloned repo, and you can find the results in the output folder within the cloned repository.
  - copy the generated HTML to a `docs` folder (as `index.html`) for easy serving with GitHub Pages.
  - Note: markdown and Excel report generation is also available but commented out in `build_solve-it-x.py`. Uncomment steps 6 and 7 to enable them.

* Once you understand the example, a script is also provided `scripts/init-solve-it-x.py`, that will create an extension folder structure for you to easily add new data to SOLVE-IT in a similar manner to the example. This initialisation script will look at the current SOLVE-IT knowledge base and create a series of folders based on the techniques, weaknesses and mitigations currently in the repo. These folders can be used to store additional data that can be overlayed on top of the base information in the repo. This is discussed in the Section [Writing your own extension](#Writing-your-own-extension).

* The example is also build within the GitHub repo online and published to https://solve-it-df.github.io/solve-it-x/ so you can see the effects easily live online. The repo comes with a [GitHub workflow script (`Build SOLVE-IT-X to HTML in docs folder`)](https://github.com/SOLVE-IT-DF/solve-it-x/blob/main/.github/workflows/build.yml). This can be manually run and will build the SOLVE-IT-X demo to the docs folder (served via GitHub Pages). This script will also copy into any repos you build from this template to make deployment easier.

# Explanation of the example

## The example folder structure

Look in the `examples` folder in this repository.

You will see a file: `extension_config.json` and a folder `demo_extension_data`.

- The file `extension_config.json` configures the extensions that will be loaded. This example file provides a replacement for an identical named file in the main repo. This will be copied over by `build_solve-it-x.py`. The format of this file is described below.

- The folder `demo_extension_data` was created with the script `scripts/init-solve-it-x.py` (see [below](#initial-extension-setup)) and contains sub-folders to contain techniques, weaknesses and mitigations. Each of those folders contains further sub-folders for each ID of individual techniques, weaknesses and mitigations. It also contains a python script `extension_code.py`

The folder structure is illustrated below, e.g.
```

- demo_extension_data/
  - mitigations/
    - DFM-1001/
    - DFM-1002/
    - .../
  - techniques/
    - DFT-1000/
    - DFT-1001/
    - .../
  - weaknesses/
    - DFW-1001/
    - DFW-1002/
    - .../
  - extension_code.py
```

This folder structure can be used to store additional data, for example we could add additional JSON data into each of the technique ID folders. This data can be processed to be presented on top of the base SOLVE-IT knowledge base.

## Running the example

### The quick way
Run the `build_solve-it-x.py` script with no arguments. This will clone the main SOLVE-IT repo from GitHub, copy the extension data into that clone, and then generate the HTML report. You will find the results in the `output` folder within the cloned repository.

You can also specify an alternative `extension_config.json` using the `--config` flag. This is useful for testing different extension configurations without modifying the default config file:

```
# Use the default config from the extension path
python3 build_solve-it-x.py

# Use a custom extension path
python3 build_solve-it-x.py '/path/to/my/extensions'

# Override the extension config (uses extensions from the default path but with a different config)
python3 build_solve-it-x.py --config examples/my_test_config.json

# Custom extension path with a config override
python3 build_solve-it-x.py '/path/to/my/extensions' --config '/path/to/alt_config.json'
```

### The long way
* Clone the SOLVE-IT repo to a new location
* Install any dependencies from the cloned repo's `requirements.txt`
* Manually copy the `extension_config.json` file into the cloned repo under the folder `extension_data` replacing the one that is there. Note that if you are using multiple extensions, you can't do this and you will need to manually edit the config file.
* Copy the folder `demo_extension_data` from this repo to the `extension_data` folder in the cloned SOLVE-IT repo.
* Run the HTML reporting script as normal and you will find additional data from the extension in your output.


## How do extensions work?
When you run the report generation script (e.g. `generate_html_from_kb.py`), as part of that process, the `extension_data` folder will be checked for registered extensions in `extension_config.json`, and for each registered extension, the `extension_code.py` within each extension folder will be loaded as a module.

The `extension_code.py` contains standardised named functions that will be called automatically when reports are generated, and used to add data to the standard SOLVE-IT report output. e.g. `get_html_for_technique(t_id, kb)`, `get_html_for_weakness(w_id, kb)`, etc.

In the example in this demo repository, the custom code in `get_html_for_technique(t_id, kb)` uses the KB API to retrieve technique data (including any extension data loaded from the extension's data folders), checks for an `extras` field, and returns a representation of that data in HTML.

This code extract is in the extension code for `get_html_for_technique(t_id, kb)`. You can see that you need to build an HTML string that will be added to the technique's detail panel in the generated HTML viewer:

```
def get_html_for_technique(t_id, kb=None):
    '''Gets HTML for adding to the SOLVE-IT-X for a specific technique'''
    if type(t_id) is not str:
         raise TypeError(f'id type is {type(t_id)}')

    if kb is None:
        raise ValueError("kb is None")

    # Get extension data for this technique
    technique = kb.get_technique(t_id)
    if not technique:
        return ""

    demo_ext_data = technique.get('extension_data', {}).get('Demo extension')
    if demo_ext_data and 'extras' in demo_ext_data:
        out_str = '<div style="margin-top:10px; padding:8px; background:#f0f4ff; border:1px solid #c7d2fe; border-radius:6px;">'
        out_str += f'<strong>Extras (from demo extension):</strong><br>{demo_ext_data.get("extras")}'
        out_str += '</div>'
        return out_str

    return ""
```

This information (in `out_str`) is then added by the main SOLVE-IT report generation code to the technique's detail panel in the HTML viewer.


# Writing your own extension

## Initial extension setup
A script is provided: `scripts/init-solve-it-x.py`. This can be used to initialise a folder that will contain extensions, and/or a folder that will contain an extension.

For example, to create a folder for extensions, you can run:

```
python3 scripts/init-solve-it-x.py --setup-extensions-base-folder --path '/Users/user/dev/solve-it-x-demo/test'
```
This will create the folder if it does not yet exist, and copy over a sample `extension_config.json` with no registered extensions.

You can then use the same script with different parameters to initialise a template extension. e.g.:
```
python3 scripts/init-solve-it-x.py --init-extension --path '/Users/user/dev/solve-it-x-demo/test/demo_ext1'
```

This will create that folder if it does not exist, access the latest online repo for SOLVE-IT, read all the techniques, weaknesses and mitigations and create a folder structure that mirrors the current state of the repo, with a subfolder for each ID of techniques, weaknesses and mitigations. It will also create a template version of `extension_code.py` e.g.:

```
demo_ext1/
      ├── extension_code.py
      ├── mitigations/
      │   ├── DFM-1001/
      │   ├── DFM-1002/
      │   ├── ...
      │   └── DFM-1xxx/
      ├── techniques/
      │   ├── DFT-1000/
      │   ├── DFT-1001/
      │   ├── ...
      │   └── DFT-1xxx/
      └── weaknesses/
          ├── DFW-1001/
          ├── DFW-1002/
          ├── ...
          └── DFW-1xxx/

```

An important note is that this will *not* update the file `extension_config.json`[^1]. You will need to manually register your extension folder. To do this, modify `extension_config.json`: in particular in the `extensions` field, add the details about your extension. This example extension is named 'Demo extension 1', has a relative folder path of `demo_ext1`, and has a description field to describe in more detail what this extension does. The relevant extract is below:

[^1]: Another way to use init-solve-it-x.py is to create the base extension folder and an extension at once.
      If you use this method, this will create an updated config file for you. This alternative method can be run using:
      `python3 scripts/init-solve-it-x.py --setup-extensions-base-folder --path '/Users/user/dev/solve-it-x-demo/test' --include-extension demo1` and will create an extension named demo1.


```
"extensions":
    {
        "Demo extension 1": {
            "folder_path": "demo_ext1",
            "description": "Just a simple demo of extension use"
        }
    },
```


* Next you need to write code in the `extension_code.py` stored within your new extension folder structure. You can use the `extension_code.py` in the examples folder as a reference. In the `extension_code.py` file that has been created as part of the initialisation there are placeholder functions for HTML, markdown and Excel generation. Key HTML functions you can customise include (see example below in the section [Customising extension_code.py](#customising-extension_codepy)):
    * `get_html_generic(kb)`
    * `get_html_for_technique(t_id, kb)`
    * `get_html_for_technique_suffix(t_id, kb)`
    * `get_html_for_weakness(w_id, kb)`
    * `get_html_for_weakness_prefix(w_id, kb)` / `get_html_for_weakness_suffix(w_id, kb)`
    * `get_html_for_mitigation(m_id, kb)`
    * `get_html_for_mitigation_prefix(m_id, kb)` / `get_html_for_mitigation_suffix(m_id, kb)`

    Similar functions are available for markdown (`get_markdown_for_technique`, etc.) and Excel (`get_excel_for_technique`, etc.).

* If you need additional data, you can add content within subfolders for techniques, weaknesses and/or mitigations. The format of this is up to you, but the code you add to `extension_code.py` needs to process that data into one of the standard representations for the reporting formats.
* In addition, the file `extension_config.json` can be further modified to hide fields from the original knowledge base if they are not interesting to you for your custom reports. For example, the `examples` field can be hidden by setting the field value to `false`, as shown below.

```
    "technique_fields": {
        "id": true,
        "name": true,
        "description": true,
        "synonyms": true,
        "details": true,
        "subtechniques": true,
        "examples": false,
        "weaknesses": true,
        "CASE_input_classes": true,
        "CASE_output_classes": true,
        "references": true
    },
```

## Customising the global config

A file `global_solveit_config.py` controls the overall presentation of the HTML viewer, including status labels (e.g. "stable", "partial", "placeholder"), status colours, and technique cell colouring. A generic default is provided that uses the standard SOLVE-IT maturity-based labels.

If your extension needs custom status labels or colours, you can create your own global config file and reference it in your `extension_config.json` using the `"global_config"` field. For example, the CLI Tools extension uses a custom config that labels techniques as "has tools" / "no tools":

```
{
    "global_config": "global_solveit_config_cli_tools.py",

    "extensions": {
        "CLI Tools": {
            "folder_path": "cli_tools_extension",
            "description": "Maps open-source forensic CLI tools to techniques"
        }
    },
    ...
}
```

When `build_solve-it-x.py` runs, it reads this field and copies the specified file as `global_solveit_config.py` into the extension_data folder. If no `"global_config"` is specified, the default `global_solveit_config.py` is used.

## Customising extension_code.py
If you have followed the instructions above, you will have set up the basic structure for an extension with a folder structure that mirrors the current set of techniques, weaknesses and mitigations. As an example, to customise the content returned for a technique, we can edit `demo_ext1/extension_code.py`, in the function `get_html_for_technique(t_id)` and change it to:

```
"""HTML text to be added to the end of each technique detail panel"""
def get_html_for_technique(t_id, kb=None):
    return f"<p>This is some custom technique content for {t_id}</p>"
```

We can now use `build_solve-it-x.py` but with a custom path to the extension folder that we have built and configured (rather than using the default example path), e.g.:

```
python3 build_solve-it-x.py '/Users/user/dev/solve-it-x-demo/test'
```

When this script runs, you will see:
- the solve-it repo cloned to a `solve-it-clone` path
- the extension data from `test` copied into the extension folder of the cloned repo
- the HTML report generated in the `output` folder within the cloned repo
- the HTML copied to the `docs` folder as `index.html` for GitHub Pages


# Using different extensions and configurations

If you have multiple extensions or configurations, you can point `build_solve-it-x.py` at different folders and config files:

```
# Build using a custom extension folder
python3 build_solve-it-x.py '/path/to/my/extensions'

# Build using the default extension folder but with an alternative config
python3 build_solve-it-x.py --config '/path/to/my/extension_config.json'

# Combine a custom extension folder with a specific config
python3 build_solve-it-x.py '/path/to/my/extensions' --config '/path/to/my/extension_config.json'
```

This is useful when you maintain several extensions for different purposes (e.g. tool mappings, organisational notes, platform-specific data) and want to build them independently.

# Updating an existing extension

A script is provided: `scripts/update-solve-it-x.py`. This can be used to update an existing extension folder with any new techniques, weaknesses or mitigations that have been added to the main SOLVE-IT repository since the extension was first created. It will only add new folders and will not modify any existing data.

```
python3 scripts/update-solve-it-x.py --path '/path/to/my/extension'
```

The script will show you what new folders would be created and ask for confirmation before making changes.