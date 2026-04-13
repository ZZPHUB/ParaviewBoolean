# Paraview Boolean Operation Plugin
## Description
This plugin adds a new filter to Paraview that allows users to perform boolean operations (union, intersection, difference) on 3D geometries. The plugin is designed to be user-friendly and integrates seamlessly with the existing Paraview interface.The original vtk lib is  very unstable for boolean operations!


## Paraview Version
- 5.13(At Least This Version Is Supported)

## Installation And Usage

1. Download the plugin
2. Create Paraview Python Interpreter Environment,Like This
```\Your\Paraview\Path\bin\pvpython -m venv YourParaviewEnv```
3. Activate The Paraview Python Interpreter Environment,Like This.
```source \YourParaviewEnv\Path\bin\activate```
4. Install The Dependencies Using PIP,Like This.
```pip install manifold3d -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com```
Because My Paraview Python Interpreter Enviroment Is Not Support SSL,So I Use Aliyun Mirror With HTTP Protocol.If Your Paraview Python Interpreter Enviroment Is Support SSL,You Can Use HTTPS Protocol,Like This.
```pip install manifold3d```
5. Start Paraview With Args,Like This.
```paraview --venv \ParaviewEnv\Path\```
For Convenience,You Can Add The Paraview Environment Variable To Your System Environment Variables,Like This.
```alias pv="paraview --venv \ParaviewEnv\Path\```
6. Load The Plugin Into Paraview.
7. Enjoy The Plugin!
