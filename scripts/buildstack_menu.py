#!/usr/bin/env python3

checkedMenuItems = []
results = {}

def main():
  import os
  import time
  import yaml
  from blessed import Terminal

  # Constants
  templateDirectory = './.templates'
  serviceFile = 'service.yml'
  buildScriptFile = 'build.py'
  dockerPathOutput = './docker-compose.yml'
  dockerSavePathOutput = './services/docker-compose.save.yml'
  composeOverrideFile = './compose-override.yml'

  # Runtime vars
  menu = []
  dockerComposeYaml = {}
  templateDirectoryFolders = next(os.walk(templateDirectory))[1]
  term = Terminal()

  def buildServices():
    try:
      runPrebuildHook()
      dockerFileYaml = {}
      dockerFileYaml["version"] = "3.6"
      dockerFileYaml["services"] = {}
      dockerFileYaml["services"] = dockerComposeYaml

      if os.path.exists(composeOverrideFile):
        with open(r'%s' % composeOverrideFile) as fileOverride:
          yamlOverride = yaml.load(fileOverride, Loader=yaml.SafeLoader)

        mergedYaml = mergeYaml(yamlOverride, dockerFileYaml)
        dockerFileYaml = mergedYaml

      with open(r'%s' % dockerPathOutput, 'w') as outputFile:
        yaml.dump(dockerFileYaml, outputFile, default_flow_style=False, sort_keys=False)

      with open(r'%s' % dockerSavePathOutput, 'w') as outputFile:
        yaml.dump(dockerFileYaml, outputFile, default_flow_style=False, sort_keys=False)

      runPostbuildHook()
      return True
    except:
      return False

  def mergeYaml(priorityYaml, defaultYaml):
    if isinstance(priorityYaml, dict) and isinstance(defaultYaml, dict):
      for k, v in defaultYaml.iteritems():
        if k not in priorityYaml:
          priorityYaml[k] = v
        else:
          priorityYaml[k] = mergeYaml(priorityYaml[k], v)
    return defaultYaml

  def generateTemplateList(templateDirectoryFolders):
    templateListDirectories = []
    for directory in templateDirectoryFolders:
      serviceFilePath = templateDirectory + '/' + directory + '/' + serviceFile
      if os.path.exists(serviceFilePath):
        templateListDirectories.append(directory)

    return templateListDirectories

  templatesList = generateTemplateList(templateDirectoryFolders)
  for directory in templatesList:
    menu.append([directory, { "checked": False, "issues": None }])

  def generateLineText(text, textLength=None, paddingBefore=0, lineLength=26):
    result = ""
    for i in range(paddingBefore):
      result += " "

    textPrintableCharactersLength = textLength

    if (textPrintableCharactersLength) == None:
      textPrintableCharactersLength = len(text)

    result += text
    remainingSpace = lineLength - textPrintableCharactersLength

    for i in range(remainingSpace):
      result += " "
    
    return result

  def mainRender(menu, selection):
    paddingBefore = 4
    optionsLength = len(" >>   Options ")
    optionsIssuesSpace = len("      ")
    spaceAfterissues = len("      ")
    issuesLength = len(" !!   Issue ")

    term = Terminal()
    allIssues = []
    print(term.clear())
    print(term.move_y(term.height // 16))
    print(term.black_on_cornsilk4(term.center('IOTstack Build Menu')))
    print("")
    print(term.center("╔════════════════════════════════════════════════════════════════════════════════╗"))
    print(term.center("║                                                                                ║"))
    print(term.center("║      Select containers to build                                                ║"))
    print(term.center("║                                                                                ║"))

    checkForOptions()

    for (index, menuItem) in enumerate(menu): # Menu loop
      lineText = generateLineText(menuItem[0], paddingBefore=paddingBefore)

       # Menu highlight logic
      if index == selection:
        formattedLineText = '{t.white_on_gold4}{title}{t.normal}'.format(t=term, title=menuItem[0])
        paddedLineText = generateLineText(formattedLineText, textLength=len(menuItem[0]), paddingBefore=paddingBefore)
        toPrint = paddedLineText
      else:
        toPrint = '{title}{t.normal}'.format(t=term, title=lineText)
      # #####

      # Options and issues
      if "options" in menuItem[1] and menuItem[1]["options"]:
        toPrint = toPrint + '{t.blue_on_black} >> {t.normal}'.format(t=term)
        toPrint = toPrint + ' {t.white_on_black} Options {t.normal}'.format(t=term)
      else:
        for i in range(optionsLength):
          toPrint += " "

      for i in range(optionsIssuesSpace):
        toPrint += " "

      if "issues" in menuItem[1] and menuItem[1]["issues"]:
        toPrint = toPrint + '{t.red_on_orange} !! {t.normal}'.format(t=term)
        toPrint = toPrint + ' {t.orange_on_black} Issue {t.normal}'.format(t=term)
        allIssues.append({ "serviceName": menuItem[0], "issues": menuItem[1]["issues"] })
      else:
        if menuItem[1]["checked"]:
          if not menuItem[1]["issues"] == None and len(menuItem[1]["issues"]) == 0:
            toPrint = toPrint + '     {t.green_on_blue} Pass {t.normal} '.format(t=term)
          else:
            for i in range(issuesLength):
              toPrint += " "
        else:
          for i in range(issuesLength):
            toPrint += " "

      for i in range(spaceAfterissues):
        toPrint += " "
      # #####

      # Menu check render logic
      if menuItem[1]["checked"]:
        toPrint = "     (X) " + toPrint
      else:
        toPrint = "     ( ) " + toPrint

      toPrint = "║ " + toPrint + "  ║" # Generate border
      toPrint = term.center(toPrint) # Center Text (All lines should have the same amount of printable characters)
      # #####
      print(toPrint)

    print(term.center("║                                                                                ║"))
    print(term.center("║                                                                                ║"))
    print(term.center("║      Controls:                                                                 ║"))
    print(term.center("║      [Space] to select or deselect image                                       ║"))
    print(term.center("║      [Up] and [Down] to move selection cursor                                  ║"))
    print(term.center("║      [Right] for options for containers that support it (none at the moment)   ║"))
    print(term.center("║      [Enter] to begin build                                                    ║"))
    print(term.center("║      [Escape] to cancel build                                                  ║"))
    print(term.center("║                                                                                ║"))
    print(term.center("║                                                                                ║"))
    print(term.center("╚════════════════════════════════════════════════════════════════════════════════╝"))
    if len(allIssues) > 0:
      print(term.center(""))
      print(term.center(""))
      print(term.center(""))
      print(term.center("╔══════ Build Issues ═════════════════════════════════════════════════════════════════════════════════════════════════════════╗"))
      print(term.center("║                                                                                                                             ║"))
      for serviceIssues in allIssues:
        for index, issue in enumerate(serviceIssues["issues"]):
          spacesAndBracketsLen = 5
          issueAndTypeLen = len(issue) + len(serviceIssues["serviceName"]) + spacesAndBracketsLen
          serviceNameAndConflictType = '{t.red_on_black}{issueService}{t.normal} ({t.yellow_on_black}{issueType}{t.normal}) '.format(t=term, issueService=serviceIssues["serviceName"], issueType=issue)
          formattedServiceNameAndConflictType = generateLineText(str(serviceNameAndConflictType), textLength=issueAndTypeLen, paddingBefore=0, lineLength=49)
          issueDescription = generateLineText(str(serviceIssues["issues"][issue]), textLength=len(str(serviceIssues["issues"][issue])), paddingBefore=0, lineLength=72)
          print(term.center("║ {} - {} ║".format(formattedServiceNameAndConflictType, issueDescription) ))
      print(term.center("║                                                                                                                             ║"))
      print(term.center("╚═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝"))

    return

  def setCheckedMenuItems():
    global checkedMenuItems
    checkedMenuItems.clear()
    for (index, menuItem) in enumerate(menu):
      if menuItem[1]["checked"]:
        checkedMenuItems.append(menuItem[0])

  def loadServices():
    dockerComposeYaml.clear()
    for (index, checkedMenuItem) in enumerate(checkedMenuItems):
      serviceFilePath = templateDirectory + '/' + checkedMenuItem + '/' + serviceFile
      with open(r'%s' % serviceFilePath) as yamlServiceFile:
        dockerComposeYaml[checkedMenuItem] = yaml.load(yamlServiceFile, Loader=yaml.SafeLoader)[checkedMenuItem]

    return True

  def checkForIssues():
    global dockerComposeYaml
    for (index, checkedMenuItem) in enumerate(checkedMenuItems):
      buildScriptPath = templateDirectory + '/' + checkedMenuItem + '/' + buildScriptFile
      if os.path.exists(buildScriptPath):
          with open(buildScriptPath, "rb") as pythonDynamicImportFile:
            code = compile(pythonDynamicImportFile.read(), buildScriptPath, "exec")
          execGlobals = {
            "dockerComposeYaml": dockerComposeYaml,
            "toRun": "checkForRunChecksHook",
            "currentServiceName": checkedMenuItem
          }
          execLocals = locals()
          exec(code, execGlobals, execLocals)
          if "buildHooks" in execGlobals and "runChecksHook" in execGlobals["buildHooks"] and execGlobals["buildHooks"]["runChecksHook"]:
            execGlobals = {
              "dockerComposeYaml": dockerComposeYaml,
              "toRun": "runChecks",
              "currentServiceName": checkedMenuItem
            }
            execLocals = locals()
            exec(code, execGlobals, execLocals)
            if "issues" in execGlobals and len(execGlobals["issues"]) > 0:
              menu[getMenuItemIndexByService(checkedMenuItem)][1]["issues"] = execGlobals["issues"]
            else:
              menu[getMenuItemIndexByService(checkedMenuItem)][1]["issues"] = []
          else:
            menu[getMenuItemIndexByService(checkedMenuItem)][1]["issues"] = []

  def checkForOptions():
    for (index, menuItem) in enumerate(menu):
      buildScriptPath = templateDirectory + '/' + menuItem[0] + '/' + buildScriptFile
      if os.path.exists(buildScriptPath):
          with open(buildScriptPath, "rb") as pythonDynamicImportFile:
            code = compile(pythonDynamicImportFile.read(), buildScriptPath, "exec")
          execGlobals = {
            "dockerComposeYaml": dockerComposeYaml,
            "toRun": "checkForOptionsHook",
            "currentServiceName": menuItem[0]
          }
          execLocals = locals()
          exec(code, execGlobals, execLocals)
          if "options" in execGlobals["buildHooks"] and execGlobals["buildHooks"]["options"]:
            menu[getMenuItemIndexByService(menuItem[0])][1]["options"] = True

  def runPrebuildHook():
    for (index, checkedMenuItem) in enumerate(checkedMenuItems):
      buildScriptPath = templateDirectory + '/' + checkedMenuItem + '/' + buildScriptFile
      if os.path.exists(buildScriptPath):
          with open(buildScriptPath, "rb") as pythonDynamicImportFile:
            code = compile(pythonDynamicImportFile.read(), buildScriptPath, "exec")
          execGlobals = {
            "dockerComposeYaml": dockerComposeYaml,
            "toRun": "checkForPreBuildHook",
            "currentServiceName": checkedMenuItem
          }
          execLocals = locals()
          exec(code, execGlobals, execLocals)
          if "preBuildHook" in execGlobals["buildHooks"] and execGlobals["buildHooks"]["preBuildHook"]:
            execGlobals = {
              "dockerComposeYaml": dockerComposeYaml,
              "toRun": "preBuild",
              "currentServiceName": checkedMenuItem
            }
            execLocals = locals()
            exec(code, execGlobals, execLocals)

  def runPostbuildHook():
    for (index, checkedMenuItem) in enumerate(checkedMenuItems):
      buildScriptPath = templateDirectory + '/' + checkedMenuItem + '/' + buildScriptFile
      if os.path.exists(buildScriptPath):
          with open(buildScriptPath, "rb") as pythonDynamicImportFile:
            code = compile(pythonDynamicImportFile.read(), buildScriptPath, "exec")
          execGlobals = {
            "dockerComposeYaml": dockerComposeYaml,
            "toRun": "checkForPostBuildHook",
            "currentServiceName": checkedMenuItem
          }
          execLocals = locals()
          exec(code, execGlobals, execLocals)
          if "postBuildHook" in execGlobals["buildHooks"] and execGlobals["buildHooks"]["postBuildHook"]:
            execGlobals = {
              "dockerComposeYaml": dockerComposeYaml,
              "toRun": "postBuild",
              "currentServiceName": checkedMenuItem
            }
            execLocals = locals()
            exec(code, execGlobals, execLocals)

  def executeServiceOptions():
    menuItem = menu[selection]
    if "buildHooks" in menuItem[1] and "options" in menuItem[1]["buildHooks"] and menuItem[1]["buildHooks"]["options"]:
      buildScriptPath = templateDirectory + '/' + menuItem[0] + '/' + buildScriptFile
      if os.path.exists(buildScriptPath):
          with open(buildScriptPath, "rb") as pythonDynamicImportFile:
            code = compile(pythonDynamicImportFile.read(), buildScriptPath, "exec")
          execGlobals = {
            "dockerComposeYaml": dockerComposeYaml,
            "toRun": "runOptionsMenu",
            "currentServiceName": menuItem[0]
          }
          execLocals = locals()
          exec(code, execGlobals, execLocals)

  def getMenuItemIndexByService(serviceName):
    for (index, menuItem) in enumerate(menu):
      if (menuItem[0] == serviceName):
        return index

  def checkMenuItem(selection):
    if menu[selection][1]["checked"] == True:
      menu[selection][1]["checked"] = False
      menu[selection][1]["issues"] = None
    else:
      menu[selection][1]["checked"] = True

  def prepareMenuState():
    global dockerComposeYaml
    for (index, serviceName) in enumerate(dockerComposeYaml):
      checkMenuItem(getMenuItemIndexByService(serviceName))
      setCheckedMenuItems()
      checkForIssues()

    return True

  def loadCurrentConfigs():
    global dockerComposeYaml
    if os.path.exists(dockerSavePathOutput):
      with open(r'%s' % dockerSavePathOutput) as fileSavedConfigs:
        previousConfigs = yaml.load(fileSavedConfigs, Loader=yaml.SafeLoader)
        if "services" in previousConfigs:
          dockerComposeYaml = previousConfigs["services"]
          return True
    return False

  if __name__ == '__main__':
    global results
    term = Terminal()
    with term.fullscreen():
      selection = 0
      if loadCurrentConfigs():
        prepareMenuState()
      mainRender(menu, selection)
      selectionInProgress = True
      with term.cbreak():
        while selectionInProgress:
          key = term.inkey()
          if key.is_sequence:
            if key.name == 'KEY_TAB':
              selection += 1
            if key.name == 'KEY_DOWN':
              selection += 1
            if key.name == 'KEY_UP':
              selection -= 1
            if key.name == 'KEY_RIGHT':
              executeServiceOptions()
            if key.name == 'KEY_ENTER':
              setCheckedMenuItems()
              loadServices()
              checkForIssues()
              selectionInProgress = False
              results["buildState"] = buildServices()
              return results["buildState"]
            if key.name == 'KEY_ESCAPE':
              results["buildState"] = False
              return results["buildState"]
          elif key:
            if key == ' ': # Space pressed
              checkMenuItem(selection)
              setCheckedMenuItems()
              loadServices()
              checkForIssues()
            else:
              print("got {0}.".format((str(key), key.name, key.code)))
              time.sleep(0.1)

          selection = selection % len(menu)

          mainRender(menu, selection)

main()