//
//  CommandLine.cs
//
//  Lunar Unity Mobile Console
//  https://github.com/SpaceMadness/lunar-unity-console
//
//  Copyright 2015-2021 Alex Lementuev, SpaceMadness.
//
//  Licensed under the Apache License, Version 2.0 (the "License");
//  you may not use this file except in compliance with the License.
//  You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
//  Unless required by applicable law or agreed to in writing, software
//  distributed under the License is distributed on an "AS IS" BASIS,
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//  See the License for the specific language governing permissions and
//  limitations under the License.
//


﻿using System;
using System.Collections.Generic;
using System.IO;

namespace LunarConsoleEditorInternal
{
    internal static class CommandLine
    {
        public static IDictionary<string, string> Arguments
        {
            get
            {
                var parsedArgs = new Dictionary<string, string>();
                var commandLineArgs = Environment.GetCommandLineArgs();
                for (var i = 0; i < commandLineArgs.Length; i++)
                {
                    if (commandLineArgs[i].StartsWith("-") && commandLineArgs[i].Length > 1)
                    {
                        var key = commandLineArgs[i].Substring(1);
                        string value = null;

                        if (i + 1 < commandLineArgs.Length && !commandLineArgs[i + 1].StartsWith("-"))
                        {
                            value = commandLineArgs[i + 1];
                            i++;
                        }

                        parsedArgs[key] = value;
                    }
                }

                return parsedArgs;
            }
        }
    }
}