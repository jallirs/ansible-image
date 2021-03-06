import os
import subprocess
import os
import shlex

#CPU'S List
ISOLCPU_LIST = "4,5,6,7,48,49,50,51"

#Various Grubs
grubs = { "/mnt/etc/default/grub.ucf-dist",
          "/mnt/etc/default/grub",
          "/mnt/etc/default/grub.d/50-curtin-settings.cfg"
        }



DOCUMENTATION = '''
module: grubconf
version_added: historical
short_description: Editing GRUB config files (/etc/grub.conf)
description:
     - Adds and removes kernel flags from /etc/grub.conf in a repeatable way.
options:
  file:
    description:
      - "The grub.conf file to edit."
    required: false
    default: "/etc/grub.conf"
  flag:
    description:
      - "The name of the kernel flag. Can either be KEY or KEY=VALUE formatted."
    required: true
    default: null
    aliases: [ 'name' ]
  state:
    description:
      - Whether to add/set (C(present)), or remove (C(absent)) the flag.
    required: false
    choices: [ "present", "absent"]
    default: "present"
  value:
    description:
      - If the flag to be changed is of the KEY=VALUE type, this parameter
        specifies the value for the flag (if the flag is already set with a
        different value, it overrides the existing flag)
    required: false
    default: null
    aliases: []
# informational: requirements for nodes
requirements: [ ]
author:
    - "Palette Software / Starschema"
    - "Gyula Laszlo"
    - "Edited by Randeep Jalli"
'''

EXAMPLES = '''
- name: Add 'transparent_hugepages=never' to the kernel flags
  grubconfig: flag=transparent_hugepages value=never
- name: Remove the 'rhgb' flag from the kernel flags
  grubconfig: flag=rhgb state=absent
- name: Add the 'quiet' flag
  grubconfig: flag=quiet state=present
'''



# for this module, we're going to do key=value style arguments
# this is up to each module to decide what it wants, but all
# core modules besides 'command' and 'shell' take key=value
# so this is highly recommended


StateRoot = 0
# We are in a title
StateTitle = 5

# A comment
KindComment = 0
# A single root-based property
KindProp = 1
# A title
KindTitle = 2
KindTitleProp = 3
KindTitleKernelFlags = 4
TITLE_INDENT = "\t"
grub_args = { "flag"  : "isolcpus",
              "value" : ISOLCPU_LIST,
              "state" : "present",
              "grubfiles" : grubs }

class GrubLine:
    def __init__(self, kind, data, children):
        self.kind = kind
        self.data = data
        self.children = children

class GrubKernelFlag:
    def __init__(self, value_str):
        # if there is an eq sign in the value then its a pair
        (self.key, self.value) = (None, None)
        value = value_str.strip()
        self.is_kv = "=" in value
        if self.is_kv:
            (self.key, self.value) = value.split("=", 1)
        else:
            self.key = value_str

    def __str__(self):
        if self.is_kv:
            return "{0}={1}".format(self.key, self.value)
        else:
            return self.key




class GrubKernelFlags:
    def __init__(self, line):
        # cut off the 'kernel' prefix and the extra spaces
        flags_line = line.strip()[6:].strip()
        self.flags = []
        for flagval in shlex.split( flags_line ):
            self.flags.append( GrubKernelFlag( flagval ))

    def __str__(self):
        return " ".join([str(flag) for flag in self.flags])

    def _find_flag_by_key(self, key):
        # Find the matching key
        for flag in self.flags:
            if flag.key == key:
                return flag
        return None


    # Tries to update a flag in the current flag line.
    # returns True if update happened
    def update_flag(self, flagval, state):
        (key, value) = (flagval, None)
        if "=" in flagval:
            (key, value) = flagval.split("=")

        # find existing flags
        existing_flag = self._find_flag_by_key(key)

        # add to the flags if not yet there
        if state == "present":
            if existing_flag == None:
                self.flags.append( GrubKernelFlag( flagval ) )
                return True
            else:
                # update the value if already there (if its not a kv-type, if
                # its a flag-type, do nothing)
                if existing_flag.is_kv:
                    if existing_flag.value != value:
                        existing_flag.value = value
                        return True


        # If the flag needs to be removed, our job is simple
        if state == "absent":
            if existing_flag != None:
                self.flags.remove( existing_flag )
                return True

        return False







class GrubConfig:
    def __init__(self, grub_file):
        self.grub_file = grub_file
        self.grub_data = None
        self._load_grub_conf(grub_file)


    # Tries to load a grub file
    def _load_grub_conf(self, grub_file):

        # Read all lines from the file
        lines = [line.rstrip('\n') for line in open(grub_file)]

        state = StateRoot
        context = []
        contextStack = []

        for line in lines:
            # Remove any string prefixes
            raw_line = line.lstrip()

            # If the line starts with empty characters,
            # change the state to signal that we are no longer in a 'title'
            if state == StateTitle and len(raw_line) == len(line):
                state = StateRoot
                context = contextStack.pop()

            # find titles
            if state == StateRoot and line.startswith("title"):
                state = StateTitle
                titleContext = []
                context.append( GrubLine(KindTitle, line[5:].strip(), titleContext))
                contextStack.append(context)
                context = titleContext
                continue


            # find comments
            if line.startswith("#"):
                context.append( GrubLine(KindComment, line, None))
                continue

            # if we are in the root we have flags
            if state == StateRoot:
                context.append( GrubLine(KindProp, line, None))
                continue


            # if we are in a title, check for kernel flags
            if state == StateTitle and raw_line.startswith("kernel"):
                context.append( GrubLine(KindTitleKernelFlags, line, GrubKernelFlags( line )))
                if False:
                    kernelFlag = GrubKernelFlag( line )
                    flags_line = Vraw_line[6:].strip()

                    flagList = []
                    # split the line with shlex
                    for flagval in shlex.split( flags_line ):
                        flagList.append({ "value": flagval })


                    context.append( GrubLine(KindTitleKernelFlags, flags_line, flagList))
                continue

            if state == StateTitle:
                context.append( GrubLine(KindTitleProp, raw_line, None))
                continue


        # if we are still in a title state, move back (as we should for EOL)
        if state == StateTitle:
            context = contextStack.pop()

        self.grub_data = context


    def __str__(self):
        if self.grub_data == None:
            return ""

        lines = []
        for line in self.grub_data:
            if line.kind == KindProp:
                lines.append( line.data )
            elif line.kind == KindComment:
                lines.append(line.data)
            elif line.kind == KindTitle:
                lines.append("title {0}".format(line.data))
                for child in line.children:
                    if child.kind == KindTitleProp:
                        lines.append("{0}{1}".format(TITLE_INDENT, child.data))
                    elif child.kind == KindComment:
                        lines.append(child.data)
                    elif child.kind == KindTitleKernelFlags:
                        lines.append("{0}kernel {1}".format( TITLE_INDENT, child.children))
        return "\n".join(lines)



    # Tries to update a flag in Grub. Returns True if it changed anything
    def update_flag(self, kernel_flag, state):
        has_changes = False
        # if its a 'key=value' type flag
        for line in self.grub_data:
            # only update kernel flags for titles
            if line.kind == KindTitle:
                for child in line.children:
                    if child.kind == KindTitleKernelFlags:
                        has_changes = has_changes or child.children.update_flag(kernel_flag,state)

        return has_changes


    def save(self):
        with open(self.grub_file, "w") as f:
            f.write(str(self))



def run_command():
    # Get the flag name to set
    flag_value = grub_args['flag']
    # if we have a value use that as value, otherwise we aree simply setting a flag
    if "value" in grub_args:
        flag_value = "{0}={1}".format(grub_args['flag'], grub_args['value'])
    
    did_updates = False
    # Start the actual work
    for grubfile in grub_args['grubfiles']:
      if( os.path.exists(grubfile) ):
        try:
            grubconf = GrubConfig(grubfile)
            did_updates = grubconf.update_flag(flag_value, grub_args['state'])
            grubconf.save()

            # Show if we did something
            print("changed grub file " + grubfile)

        except Exception as e:

            print("something bad happened while editing " + grubfile )
      else:
        print("file doesn't exist ")

    # If we changed the grub conf, make sure we run update-grub, if we cannot run it properly
    # we leave
    if did_updates:
      os.chroot("/mnt")
      if os.getuid() == 0:
        subprocess.check_call(["update-grub"])
        print("changed to running as root, ran update-grub done")
        exit()
      else:
        exit(1)



# import module snippets
if __name__ == '__main__':
    run_command()
