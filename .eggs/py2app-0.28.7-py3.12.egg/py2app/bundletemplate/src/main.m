//
//  main.m
//  apptemplate
//
//  Created by Bob Ippolito on Mon September 20 2004.
//  Copyright (c) 2004 Bob Ippolito. All rights reserved.
//

#import <Foundation/Foundation.h>
#include <mach-o/dyld.h>
#include <mach-o/loader.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/syslimits.h>
#include <crt_externs.h>
#include <wchar.h>
#include <locale.h>
#include <langinfo.h>

#include <objc/objc-class.h>

#pragma clang diagnostic ignored "-Wdeprecated-declarations"

//
// Constants
//
NSString *ERR_CANNOT_SAVE_LOCALE = @"Cannot save locale information";
NSString *ERR_REALLYBADTITLE = @"The bundle could not be launched.";
NSString *ERR_TITLEFORMAT = @"%@ has encountered a fatal error, and will now terminate.";
NSString *ERR_PYRUNTIMELOCATIONS = @"The Info.plist file must have a PyRuntimeLocations array containing string values for preferred Python runtime locations.  These strings should be \"otool -L\" style mach ids; \"@executable_stub\" and \"~\" prefixes will be translated accordingly.";
NSString *ERR_NOPYTHONRUNTIME = @"A Python runtime could be located.  You may need to install a framework build of Python, or edit the PyRuntimeLocations array in this bundle's Info.plist file.\rThese runtime locations were attempted:\r\r";
NSString *ERR_NOPYTHONSCRIPT = @"A main script could not be located in the Resources folder.\rThese files were tried:\r\r";
NSString *ERR_LINKERRFMT = @"An internal error occurred while attempting to link with:\r\r%s\r\rSee the Console for a detailed dyld error message";
NSString *ERR_PYTHONEXCEPTION = @"An uncaught exception was raised during execution of the main script:\r\r%@: %@\r\rThis may mean that an unexpected error has occurred, or that you do not have all of the dependencies for this bundle.";
NSString *ERR_COLONPATH = @"Python bundles can not currently run from paths containing a '/' (or ':' from the Terminal).";

#define PYMACAPP_NSIMAGEFLAGS (NSADDIMAGE_OPTION_RETURN_ON_ERROR | NSADDIMAGE_OPTION_WITH_SEARCHING)
#define PYMACAPP_NSLOOKUPSYMBOLINIMAGEFLAGS (NSLOOKUPSYMBOLINIMAGE_OPTION_BIND | NSLOOKUPSYMBOLINIMAGE_OPTION_RETURN_ON_ERROR)

//
// Typedefs
//

#define Py_file_input 257
typedef int PyObject;
typedef int PyThreadState;
typedef enum {PyGILState_LOCKED, PyGILState_UNLOCKED} PyGILState_STATE;
typedef PyGILState_STATE (*PyGILState_EnsurePtr)(void);
typedef void (*PyGILState_ReleasePtr)(PyGILState_STATE);
typedef PyThreadState *(*PyEval_SaveThreadPtr)(void);
typedef void (*PyErr_ClearPtr)(void);
typedef void (*PyErr_PrintPtr)(void);
typedef int (*PyErr_OccurredPtr)(void);
typedef PyObject *(*PyBytes_FromStringPtr)(const char *);
typedef int (*PyList_InsertPtr)(PyObject *, int, PyObject *);
typedef void (*Py_DecRefPtr)(PyObject *);
typedef void (*Py_SetProgramNamePtr)(const wchar_t *);
typedef int (*Py_IsInitializedPtr)(void);
typedef void (*Py_InitializePtr)(void);
typedef void (*PyEval_InitThreadsPtr)(void);
typedef PyObject *(*PyRun_FilePtr)(FILE *, const char *, int, PyObject *, PyObject *);
typedef PyObject *(*PySys_GetObjectPtr)(const char *);
typedef int *(*PySys_SetArgvPtr)(int argc, char **argv);
typedef PyObject *(*PyObject_StrPtr)(PyObject *);
typedef const char *(*PyBytes_AsStringPtr)(PyObject *);
typedef PyObject *(*PyObject_GetAttrStringPtr)(PyObject *, const char *);
typedef PyObject *(*PyObject_CallMethodPtr)(PyObject *, const char *, const char *, ...);
typedef PyObject *(*PyImport_ImportModulePtr)(char *);
typedef PyObject *(*PyImport_AddModulePtr)(char *);
typedef PyObject *(*PyModule_AddStringConstantPtr)(PyObject *, char *, char *);
typedef PyObject *(*PyModule_AddObjectPtr)(PyObject *, char *, PyObject *);
typedef PyObject *(*PyModule_GetDictPtr)(PyObject *);
typedef void (*PyObject_SetItemPtr)(PyObject *, PyObject *, PyObject *);
typedef wchar_t* (*_Py_DecodeUTF8_surrogateescapePtr)(const char *s, ssize_t size, ssize_t*);
typedef wchar_t* (*Py_DecodeLocalePtr)(const char *s, ssize_t* size);


//
// Signatures
//

static void DefaultDecRef(PyObject *op);
static int report_error(NSString *err);
static int report_linkEdit_error(const char* name);
static int report_script_error(NSString *err, NSString *errClassName, NSString *errName);
static NSString *pyStandardizePath(NSString *pyLocation);
static BOOL doesPathExist(NSString *path);
static NSString *getBundleName(void);
static NSString *getErrorTitle(NSString *bundleName);
static const char *bundlePath(void);
static NSBundle *bundleBundle(void);
static int pyobjc_main(int argc, char * const *argv, char * const *envp);

//
// Mach-O Constructor
//

static void __attribute__ ((constructor)) _py2app_bundle_load(void);

//
// Implementation
//

static
const char *bundlePath(void) {
    int i;
    const struct mach_header *myHeader = _dyld_get_image_header_containing_address(&bundlePath);
    int count = _dyld_image_count();
    for (i = 0; i < count; i++) {
        if (_dyld_get_image_header(i) == myHeader) {
            return _dyld_get_image_name(i);
        }
    }
    abort();
    return NULL;
}

static
NSBundle *bundleBundle(void) {
    static NSBundle *myBundle = NULL;
    if (!myBundle) {
        int i;
        NSString *path = [NSString stringWithUTF8String:bundlePath()];
        // strip Contents/MacOS/App
        for (i = 0; i < 3; i++) {
            path = [path stringByDeletingLastPathComponent];
        }
        myBundle = [[NSBundle alloc] initWithPath:path];
    }
    return myBundle;
}

//
// THIS WILL NOT WORK WITH Py_TRACE_REFS / Py_DEBUG ON UNLESS USING 2.4 OR LATER!
//
static
void DefaultDecRef(PyObject *op) {
    if (op != NULL) {
        --(*op);
    }
}

static
int report_script_error(NSString *err, NSString *errClassName, NSString *errName) {
    return report_error(err);
}

static
int report_error(NSString *err) {
    NSLog(@"%@", getErrorTitle(getBundleName()));
    NSLog(@"%@", err);
    return -1;
}

static
int report_linkEdit_error(const char* name) {
    NSLinkEditErrors errorClass;
    int errorNumber;
    const char *fileName;
    const char *errorString;
    NSLinkEditError(&errorClass, &errorNumber, &fileName, &errorString);
    NSLog(@"%s: %s", name, errorString);
    printf("<<<py2app>>>> %s: %s\n", name, errorString);
    return report_error([NSString stringWithFormat:ERR_LINKERRFMT, fileName]);
}

static
NSString *pyStandardizePath(NSString *pyLocation) {
        if ([pyLocation hasPrefix:@"@executable_path/"]) {
            NSMutableArray *newComponents = [[pyLocation pathComponents] mutableCopy];
            [newComponents replaceObjectAtIndex:0 withObject:[bundleBundle() privateFrameworksPath]];
            pyLocation = [NSString pathWithComponents: newComponents];
        }
        return [pyLocation stringByStandardizingPath];
};

static
BOOL doesPathExist(NSString *path) {
        struct stat sb;
        return (stat([path fileSystemRepresentation], &sb) == -1) ? NO : YES;
}

static
NSString *getBundleName(void) {
    NSDictionary *infoDictionary = [bundleBundle() infoDictionary];
    NSString *bundleName = [infoDictionary objectForKey:@"CFBundleName"];
    if (!bundleName) {
        bundleName = [infoDictionary objectForKey:@"CFBundleExecutable"];
    }
    return bundleName;
}

static
NSString *getErrorTitle(NSString *bundleName) {
    if (!bundleName) {
        return ERR_REALLYBADTITLE;
    }
    return [NSString stringWithFormat:ERR_TITLEFORMAT,bundleName];
}

static
NSString *getPythonLocation(NSArray *pyLocations) {
    // get the runtime locations from the Info.plist

    //  *does not* inspect DYLD environment variables for overrides, fallbacks, suffixes, etc.
    //  I don't really consider that a very bad thing, as it makes this search extremely deterministic.
    //  Note that I use the env variables when the image is actually linked, so what you find here
    //  may not be what gets linked.  If this is the case, you deserve it :)

    // find a Python runtime
    NSString *pyLocation;
    NSEnumerator *pyLocationsEnumerator = [pyLocations objectEnumerator];
    while ((pyLocation = [pyLocationsEnumerator nextObject])) {
        pyLocation = pyStandardizePath(pyLocation);
        if (doesPathExist(pyLocation)) {
            return pyLocation;
        }
    }
    return nil;
}

static NSString* getPythonInterpreter(NSString* pyLocation) {
    NSBundle* bndl;
    NSString* auxName;

    bndl = bundleBundle();

    auxName = [[bndl infoDictionary] objectForKey:@"PyExecutableName"];
    if (!auxName) {
       auxName = @"python";
    }
    return [bndl pathForAuxiliaryExecutable:auxName];
}


static
NSArray *getPythonPathArray(NSDictionary *infoDictionary, NSString *resourcePath) {
    NSMutableArray *pythonPathArray = [NSMutableArray arrayWithObject: resourcePath];
    NSArray *pyResourcePackages = [infoDictionary objectForKey:@"PyResourcePackages"];
    if (pyResourcePackages != nil) {
        NSString *pkg;
        NSEnumerator *pyResourcePackageEnumerator = [pyResourcePackages objectEnumerator];
        while ((pkg = [pyResourcePackageEnumerator nextObject])) {
            pkg = [pkg stringByExpandingTildeInPath];
            if (![@"/" isEqualToString: [pkg substringToIndex:1]]) {
                pkg = [resourcePath stringByAppendingPathComponent:pkg];
            }
            [pythonPathArray addObject:pkg];
        }
    }
    return pythonPathArray;
}

static
NSString *getMainPyPath(NSDictionary *infoDictionary) {
    NSArray *possibleMains = [infoDictionary objectForKey:@"PyMainFileNames"];
    if ( !possibleMains )
        possibleMains = [NSArray array];
    // find main python file.  __main__.py seems to be a standard, so we'll go ahead and add defaults.
    possibleMains = [possibleMains arrayByAddingObjectsFromArray:[NSArray arrayWithObjects:
        @"__main__",
        @"__realmain__",
        @"Main",
        nil]];
    NSEnumerator *possibleMainsEnumerator = [possibleMains objectEnumerator];
    NSString *mainPyPath = nil;
    NSString *nextFileName = nil;
    NSString *nextExtension = nil;
    NSArray *extensions = [NSArray arrayWithObjects:@".py", @".pyc", @".pyo", @"", nil];

    NSMutableArray *runtimeAttempts = [NSMutableArray array];
    while ((nextFileName = [possibleMainsEnumerator nextObject])) {
        NSEnumerator *nextExtensionEnumerator = [extensions objectEnumerator];
        while ((nextExtension = [nextExtensionEnumerator nextObject])) {
            [runtimeAttempts addObject:[nextFileName stringByAppendingString:nextExtension]];
        }
    }
    possibleMainsEnumerator = [runtimeAttempts objectEnumerator];
    while ((nextFileName = [possibleMainsEnumerator nextObject]) && !mainPyPath) {
            mainPyPath = [bundleBundle() pathForResource:nextFileName ofType:nil];
    }
    if (!mainPyPath) {
        NSString *components = [runtimeAttempts componentsJoinedByString:@"\r"];
        report_error([ERR_NOPYTHONSCRIPT stringByAppendingString:components]);
    }
    return mainPyPath;
}


int pyobjc_main(int argc, char * const *argv, char * const *envp) {
    char* curenv;
    char* curlocale;
    NSDictionary *infoDictionary = [bundleBundle() infoDictionary];

    if (getenv("PYTHONOPTIMIZE") != NULL) {
        unsetenv("PYTHONOPTIMIZE");
    }
    if (getenv("PYTHONDEBUG") != NULL) {
        unsetenv("PYTHONDEBUG");
    }
    if (getenv("PYTHONDONTWRITEBYTECODE") != NULL) {
        unsetenv("PYTHONDONTWRITEBYTECODE");
    }
    if (getenv("PYTHONIOENCODING") != NULL) {
        unsetenv("PYTHONIOENCODING");
    }
    if (getenv("PYTHONDUMPREFS") != NULL) {
        unsetenv("PYTHONDUMPREFS");
    }
    if (getenv("PYTHONMALLOCSTATS") != NULL) {
        unsetenv("PYTHONMALLOCSTATS");
    }

    /* Disable writing of bytecode files */
    setenv("PYTHONDONTWRITEBYTECODE", "1", 1);

    NSString *pyLocation = nil;
    while (NSIsSymbolNameDefined("_Py_Initialize")) {
        // Python is already in-process
        NSSymbol sym = NSLookupAndBindSymbol("_Py_Initialize");
        if (!sym) {
            break;
        }
        NSModule mod = NSModuleForSymbol(sym);
        if (!mod) {
            break;
        }
        const char *python_dylib_path = NSLibraryNameForModule(mod);
        if (python_dylib_path) {
            pyLocation = [NSString stringWithUTF8String:python_dylib_path];
        }
        break;
    }
    NSArray *pyLocations = [infoDictionary objectForKey:@"PyRuntimeLocations"];
    if (!pyLocation) {
        // Python is not in-process
        if (!pyLocations) {
            return report_error(ERR_PYRUNTIMELOCATIONS);
        }
        pyLocation = getPythonLocation(pyLocations);
    }
    if (!pyLocation) {
        NSString *components = [pyLocations componentsJoinedByString:@"\r\r"];
        return report_script_error([ERR_NOPYTHONRUNTIME stringByAppendingString:components], nil, nil);
    }

    // Find our resource path and possible PYTHONPATH
    NSString *resourcePath = [bundleBundle() resourcePath];
    NSArray *pythonPathArray = getPythonPathArray(infoDictionary, resourcePath);

    // find the main script
    NSString *mainPyPath = getMainPyPath(infoDictionary);
    if (!mainPyPath) {
        // error already reported
        return -1;
    }

    // Load the Python dylib (may have already been loaded, that is OK)
    const struct mach_header *py_dylib = NSAddImage([pyLocation fileSystemRepresentation], PYMACAPP_NSIMAGEFLAGS);
    if (!py_dylib) {
        return report_linkEdit_error([pyLocation fileSystemRepresentation]);
    }

    // Load the symbols we need from Python. We avoid lookups of unicode methods because their
    // names are mangled by Python (because of UCS2/UCS4 stuff) and looking them up reliably is
    // problematic.
    NSSymbol tmpSymbol;
#define LOOKUP_SYMBOL(NAME) \
    tmpSymbol = NSLookupSymbolInImage(py_dylib, "_" #NAME, PYMACAPP_NSLOOKUPSYMBOLINIMAGEFLAGS)
#define LOOKUP_DEFINEADDRESS(NAME, ADDRESS) \
    NAME ## Ptr NAME = (NAME ## Ptr)ADDRESS
#define LOOKUP_DEFINE(NAME) \
    LOOKUP_DEFINEADDRESS(NAME, NSAddressOfSymbol(tmpSymbol))
#define LOOKUP(NAME) \
    LOOKUP_SYMBOL(NAME); \
    if ( !tmpSymbol ) \
        return report_linkEdit_error(#NAME); \
    LOOKUP_DEFINE(NAME)

#define OPT_LOOKUP(NAME) \
    	LOOKUP_SYMBOL(NAME); \
	NAME ## Ptr NAME = NULL; \
        if (tmpSymbol) { \
	   NAME = (NAME ## Ptr)NSAddressOfSymbol(tmpSymbol); \
	}

    LOOKUP_SYMBOL(Py_DecRef);
    LOOKUP_DEFINEADDRESS(Py_DecRef, (tmpSymbol ? (void(*)(PyObject*))NSAddressOfSymbol(tmpSymbol) : &DefaultDecRef));
    LOOKUP(Py_SetProgramName);
    LOOKUP(Py_IsInitialized);
    LOOKUP(Py_Initialize);
    LOOKUP(PyErr_Clear);
    LOOKUP(PyErr_Print);
    LOOKUP(PyErr_Occurred);
    LOOKUP(PyGILState_Ensure);
    LOOKUP(PyGILState_Release);
    LOOKUP(PyEval_InitThreads);
    LOOKUP(PyRun_File);
    LOOKUP(PySys_GetObject);
    LOOKUP(PySys_SetArgv);
    LOOKUP(PyObject_Str);
    LOOKUP(PyList_Insert);
    LOOKUP(PyObject_GetAttrString);
    LOOKUP(PyObject_CallMethod);
    LOOKUP(PyImport_ImportModule);
    LOOKUP(PyImport_AddModule);
    LOOKUP(PyObject_SetItem);
    LOOKUP(PyModule_AddStringConstant);
    LOOKUP(PyModule_AddObject);
    LOOKUP(PyModule_GetDict);
    LOOKUP(PyEval_SaveThread);
    OPT_LOOKUP(_Py_DecodeUTF8_surrogateescape);
    OPT_LOOKUP(Py_DecodeLocale);


    /* PyBytes / PyString lookups depend of if we're on py3k or not */
    PyBytes_AsStringPtr PyBytes_AsString = NULL;
    PyBytes_FromStringPtr PyBytes_FromString = NULL;
    LOOKUP_SYMBOL(PyBytes_AsString);
    int isPy3k = tmpSymbol != NULL;
    if (isPy3k) {
        PyBytes_AsString = (PyBytes_AsStringPtr)NSAddressOfSymbol(tmpSymbol);
        LOOKUP_SYMBOL(PyBytes_FromString);
        PyBytes_FromString = (PyBytes_FromStringPtr)NSAddressOfSymbol(tmpSymbol);
    }
    else {
        LOOKUP_SYMBOL(PyString_AsString);
        PyBytes_AsString = (PyBytes_AsStringPtr)NSAddressOfSymbol(tmpSymbol);
        LOOKUP_SYMBOL(PyString_FromString);
        PyBytes_FromString = (PyBytes_FromStringPtr)NSAddressOfSymbol(tmpSymbol);
    }

#undef LOOKUP
#undef LOOKUP_DEFINE
#undef LOOKUP_DEFINEADDRESS
#undef LOOKUP_SYMBOL

    int was_initialized = Py_IsInitialized();

    /*
     * When apps are started from the Finder (or anywhere
     * except from the terminal), the LANG and LC_* variables
     * aren't set in the environment. This confuses Py_Initialize
     * when it tries to import the codec for UTF-8,
     * therefore explicitly set the locale.
     *
     * Also set the LC_CTYPE environment variable because Py_Initialize
     * reset the locale information using the environment :-(
     */
    if (isPy3k) {
        curlocale = setlocale(LC_ALL, NULL);
        if (curlocale != NULL) {
            curlocale = strdup(curlocale);
            if (curlocale == NULL) {
                    (void)report_error(ERR_CANNOT_SAVE_LOCALE);
                    return -1;
            }
        }
        setlocale(LC_ALL, "en_US.UTF-8");

        curenv = getenv("LC_CTYPE");
        if (!curenv) {
            setenv("LC_CTYPE", "en_US.UTF-8", 1);
        }
    }


    // Set up the environment variables to be transferred
    NSMutableDictionary *newEnviron = [NSMutableDictionary dictionary];
    [newEnviron setObject:[NSString stringWithFormat:@"%p", bundleBundle()] forKey:@"PYOBJC_BUNDLE_ADDRESS"];
    [newEnviron setObject:[NSString stringWithFormat:@"%p", bundleBundle()] forKey:[NSString
	 stringWithFormat:@"PYOBJC_BUNDLE_ADDRESS%ld", (long)getpid()]];
    [newEnviron setObject:resourcePath forKey:@"RESOURCEPATH"];
    NSMutableDictionary *oldEnviron = [NSMutableDictionary dictionary];

    // bootstrap Python with information about how to find what it needs
    // if it is not already initialized
    if (!was_initialized) {
        // $PREFIX/Python -> $PREFIX
        NSString *pythonProgramName = [pyLocation stringByDeletingLastPathComponent];
	NSString* interpreter = getPythonInterpreter(pyLocation);
	struct stat sb;

	if (lstat([interpreter fileSystemRepresentation], &sb) == 0) {
	    if(!((sb.st_mode & S_IFLNK) == S_IFLNK)) {
            	setenv("PYTHONHOME", [resourcePath fileSystemRepresentation], 1);
	    }
	} else {
            setenv("PYTHONHOME", [resourcePath fileSystemRepresentation], 1);
        }

        NSString *pyExecutableName = [infoDictionary objectForKey:@"PyExecutableName"];
        if ( !pyExecutableName ) {
            pyExecutableName = @"python";
        }

        pythonProgramName = [[pythonProgramName stringByAppendingPathComponent:@"bin"] stringByAppendingPathComponent:pyExecutableName];

        wchar_t wPythonName[PATH_MAX+1];
        if (isPy3k) {
            mbstowcs(wPythonName, [pythonProgramName fileSystemRepresentation], PATH_MAX+1);
        }
        else {
            const char *cPythonName = [pythonProgramName fileSystemRepresentation];
            memcpy(wPythonName, cPythonName, strlen(cPythonName));
        }
        Py_SetProgramName(wPythonName);
    }

    // Set new environment variables and save older ones (for nested plugin loading)
    NSEnumerator *envEnumerator = [newEnviron keyEnumerator];
    NSString *envKey;
    while ((envKey = [envEnumerator nextObject])) {
        char *keyString = (char *)[envKey UTF8String];
        char *oldValue = getenv(keyString);
        if (oldValue) {
            [oldEnviron setObject:[NSString stringWithUTF8String:oldValue] forKey:envKey];
        }
        setenv(keyString, (char *)[[newEnviron objectForKey:envKey] UTF8String], 1);
    }


    int rval = 0;
    FILE *mainPyFile = NULL;
    Py_Initialize();
    PyEval_InitThreads();

    if (isPy3k) {
        /*
         * Reset the environment and locale information
         */
        setlocale(LC_CTYPE, curlocale);
        free(curlocale);

        if (!curenv) {
            unsetenv("LC_CTYPE");
        }
    }


    PyGILState_STATE gilState = PyGILState_Ensure();

    if (was_initialized) {
        // transfer path into existing Python process
        PyObject *path = PySys_GetObject("path");
        NSEnumerator *pathEnumerator = [pythonPathArray reverseObjectEnumerator];
        NSString *curPath;
        while ((curPath = [pathEnumerator nextObject])) {
            PyObject *b = PyBytes_FromString([curPath UTF8String]);
            PyObject *s = PyObject_CallMethod(b, "decode", "s", "utf-8");
            PyList_Insert(path, 0, s);
            Py_DecRef(b);Py_DecRef(s);
        }

        // transfer environment variables into existing Python process
        PyObject *osModule = PyImport_ImportModule("os");
        PyObject *pyenv = PyObject_GetAttrString(osModule, "environ");
        Py_DecRef(osModule);
        envEnumerator = [newEnviron keyEnumerator];
        while ((envKey = [envEnumerator nextObject])) {
            char *keyString = (char *)[envKey UTF8String];
            PyObject *b_key = PyBytes_FromString(keyString);
            PyObject *b_value = PyBytes_FromString(getenv(keyString));
            PyObject *key = PyObject_CallMethod(b_key, "decode", "s", "utf-8");
            PyObject *value = PyObject_CallMethod(b_value, "decode", "s", "utf-8");
            PyObject_SetItem(pyenv, key, value);
            Py_DecRef(b_key);Py_DecRef(key);
            Py_DecRef(b_value);Py_DecRef(value);
        }
        Py_DecRef(pyenv);
    }

    char *c_mainPyPath = (char *)[mainPyPath fileSystemRepresentation];
    mainPyFile = fopen(c_mainPyPath, "r");
    if (!mainPyFile) {
        rval = report_error([NSString stringWithFormat:@"Could not open main script %@",mainPyPath]);
        goto cleanup;
    }
    if (!was_initialized) {
	int i;
	NSMutableData *data_argv = [NSMutableData dataWithCapacity:(sizeof(char *) * argc)];
	char **argv_new = [data_argv mutableBytes];
	if (isPy3k) {
                if (Py_DecodeLocale) {
		    argv_new[0] = (char*)Py_DecodeLocale(c_mainPyPath, NULL);
                } else {
		    argv_new[0] = (char*)_Py_DecodeUTF8_surrogateescape(c_mainPyPath, strlen(c_mainPyPath), NULL);
                }
	} else  {
		argv_new[0] = c_mainPyPath;
	}
	for (i = 1; i < argc; i++) {
		if (isPy3k) {
                        if (Py_DecodeLocale) {
			     argv_new[i] = (char*)Py_DecodeLocale(argv[i], NULL);
                        } else {
			     argv_new[i] = (char*)_Py_DecodeUTF8_surrogateescape(argv[i], strlen(argv[i]), NULL);
                        }
		} else {
			argv_new[i] = argv[i];
		}
	}
	argv_new[argc] = NULL;
	PySys_SetArgv(argc, argv_new);
    }

    // create a unique moduleName by CFBundleIdentifier replacing . with _ and prepending __main__
    NSString *moduleName = [NSString stringWithFormat:@"__main__%@", [[[infoDictionary objectForKey:@"CFBundleIdentifier"] componentsSeparatedByString:@"."] componentsJoinedByString:@"_"]];
    PyObject *module = PyImport_AddModule((char *)[moduleName UTF8String]);
    if (!module) {
        rval = report_error([NSString stringWithFormat:@"Could not create module '%@'",moduleName]);
        goto cleanup;
    }
    PyModule_AddStringConstant(module, "__file__", c_mainPyPath);
    char * builtinsName = isPy3k ? "builtins" : "__builtin__";
    PyObject *builtins = PyImport_ImportModule(builtinsName);
    PyModule_AddObject(module, "__builtins__", builtins);
    PyObject *module_dict = PyModule_GetDict(module);
    if (PyErr_Occurred()) {
        goto cleanup;
    }

    PyObject *res = PyRun_File(mainPyFile, c_mainPyPath, Py_file_input, module_dict, module_dict);
    if (res) {
	    Py_DecRef(res);
    }

cleanup:
    // un-transfer the environment variables
    envEnumerator = [newEnviron keyEnumerator];
    while ((envKey = [envEnumerator nextObject])) {
        char *keyString = (char *)[envKey UTF8String];
        NSString *newValue = [oldEnviron objectForKey:envKey];
        if (newValue) {
            setenv(keyString, [newValue UTF8String], 1);
        } else {
            unsetenv(keyString);
        }
    }

    if (mainPyFile) {
        fclose(mainPyFile);
    }
    if (PyErr_Occurred()) {
        rval = -1;
        PyErr_Print();
    }
    while ( rval ) {
        PyObject *exc = PySys_GetObject("last_type");
        if ( !exc ) {
            rval = report_error([NSString stringWithFormat:ERR_PYTHONEXCEPTION,"<<PyMacAppException>>","The exception went away?"]);
            break;
        }

        PyObject *exceptionClassName = PyObject_GetAttrString(exc, "__name__");
        if ( !exceptionClassName ) {
            rval = report_error([NSString stringWithFormat:ERR_PYTHONEXCEPTION,"<<PyMacAppException>>","Could not get exception class name?"]);
            break;
        }

        PyObject *v = PySys_GetObject("last_value");
        PyObject *exceptionName = NULL;
        if ( v )
            exceptionName = PyObject_Str(v);

        PyObject *b = PyObject_CallMethod(exceptionClassName, "encode", "s", "utf-8");
        NSString *nsExceptionClassName = [NSString stringWithCString:PyBytes_AsString(b) encoding:NSUTF8StringEncoding];
        Py_DecRef(exceptionClassName);Py_DecRef(b);
        NSString *nsExceptionName;
        if ( exceptionName ) {
            PyObject *b = PyObject_CallMethod(exceptionName, "encode", "s", "utf-8");
            nsExceptionName = [NSString stringWithCString:PyBytes_AsString(b) encoding:NSUTF8StringEncoding];
            Py_DecRef(exceptionName);Py_DecRef(b);
        } else {
            nsExceptionName = @"";
        }
        rval = report_script_error([NSString stringWithFormat:ERR_PYTHONEXCEPTION, nsExceptionClassName, nsExceptionName], nsExceptionClassName, nsExceptionName);
        break;
    }
    PyErr_Clear();
    PyGILState_Release(gilState);
    if (gilState == PyGILState_LOCKED) {
        PyEval_SaveThread();
    }

    return rval;
}


static
void _py2app_bundle_load(void)
{
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    int argc = 1;
    char * const argv[] = { (char *)bundlePath(), NULL };
    char * const *envp = *_NSGetEnviron();
    (void)pyobjc_main(argc, argv, envp);
    [pool release];
}


