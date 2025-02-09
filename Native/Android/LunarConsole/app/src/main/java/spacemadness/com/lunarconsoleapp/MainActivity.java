//
//  MainActivity.java
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


package spacemadness.com.lunarconsoleapp;

import android.annotation.TargetApi;
import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

import spacemadness.com.lunarconsole.Config;
import spacemadness.com.lunarconsole.concurrent.DispatchQueue;
import spacemadness.com.lunarconsole.concurrent.DispatchTask;
import spacemadness.com.lunarconsole.console.ConsoleLogType;
import spacemadness.com.lunarconsole.console.ConsolePlugin;
import spacemadness.com.lunarconsole.console.ConsoleViewState;
import spacemadness.com.lunarconsole.console.DefaultColorFactory;
import spacemadness.com.lunarconsole.console.DefaultRichTextFactory;
import spacemadness.com.lunarconsole.console.NativePlatform;
import spacemadness.com.lunarconsole.console.RichTextFactory;
import spacemadness.com.lunarconsole.dependency.DefaultDependencies;
import spacemadness.com.lunarconsole.json.JsonDecoder;
import spacemadness.com.lunarconsole.settings.PluginSettings;

import static spacemadness.com.lunarconsole.console.ConsoleLogType.ERROR;
import static spacemadness.com.lunarconsole.console.ConsoleLogType.EXCEPTION;
import static spacemadness.com.lunarconsole.console.ConsoleLogType.LOG;
import static spacemadness.com.lunarconsole.console.ConsoleLogType.WARNING;

public class MainActivity extends Activity {
    private static final String TEST_PREFS_NAME = "spacemadness.com.lunarconsole.Preferences";

    private static final String KEY_TEXT_DELAY = "delay";
    private static final String KEY_TEXT_CAPACITY = "capacity";
    private static final String KEY_TEXT_TRIM = "trim";
    private static final String KEY_CHECKBOX_USE_MAIN_THREAD = "use_main_thread";
    private static final String KEY_CHECKBOX_ENABLE_STACK_TRACE = "enable_stack_trace";

    private ConsolePlugin consolePlugin;
    private Thread loggerThread;
    private int logIndex;

    private EditText delayEditText;
    private EditText capacityEditText;
    private EditText trimEditText;
    private CheckBox useMainThreadCheckBox;
    private CheckBox enableStackTraceCheckBox;

    private DispatchQueue mainQueue;
    private DispatchQueue backgroundQueue;

    // UI-testing
    static boolean forceSyncCalls = false;             // don't use queues for any plugin calls
    static boolean shutdownPluginWhenDestroyed = true; // keep plugin instance when activity is destroyed

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Config.DEBUG = true;

        DefaultDependencies.register();

        mainQueue = DispatchQueue.mainQueue();
        backgroundQueue = DispatchQueue.createSerialQueue("background");

        delayEditText = findViewById(R.id.test_edit_text_delay);
        capacityEditText = findViewById(R.id.test_edit_text_capacity);
        trimEditText = findViewById(R.id.test_edit_text_trim);
        useMainThreadCheckBox = findViewById(R.id.test_checkbox_use_main_thread);
        enableStackTraceCheckBox = findViewById(R.id.test_checkbox_enable_stack_trace);

        restoreUIState();

        final int capacity = Integer.parseInt(capacityEditText.getText().toString());
        final int trim = Integer.parseInt(trimEditText.getText().toString());

        dispatchOnSelectedQueue(new DispatchTask() {
            @Override
            protected void execute() {
                if (!shutdownPluginWhenDestroyed) {
                    if (consolePlugin != null) {
                        consolePlugin.destroy(); // kill any previous instance
                    }
                }

                final String settingsJson = readTextAsset("settings.json");
                final PluginSettings settings = JsonDecoder.decode(settingsJson, PluginSettings.class);
                final Activity activity = MainActivity.this;

                RichTextFactory richTextFactory = new DefaultRichTextFactory(new DefaultColorFactory(activity));
                consolePlugin = new ConsolePlugin(activity, new NativePlatform(activity), "0.0.0", settings, richTextFactory);
				/*
				consolePlugin.registerAction(1, "Action - A");
				consolePlugin.registerAction(3, "Action - B");
				consolePlugin.registerAction(5, "Action - C");

				consolePlugin.registerVariable(0, "String variable", "String", "test-1", "test-1", 0, false, 0, 0);
				consolePlugin.registerVariable(1, "Integer variable", "Integer", "10", "10", 0, false, 0, 0);
				consolePlugin.registerVariable(2, "Float variable", "Float", "3.14", "3.14", 0, false, 0, 0);
				consolePlugin.registerVariable(3, "Toggle variable", "Boolean", "1", "1", 0, false, 0, 0);
				consolePlugin.registerVariable(4, "Range", "Float", "6.28", "6.28", 0, true, 1.0f, 10.0f);
				consolePlugin.registerVariable(5, "Volatile", "Integer", "25", "25", Variable.FLAG_NO_ARCHIVE, true, 1.0f, 10.0f);

                consolePlugin.logMessage(LOG, "", "<color=#ff0000>red</color>");
                consolePlugin.logMessage(LOG, "", "<color=#ff00007f>red</color>");

                consolePlugin.logMessage(LOG, "", "<color=#00ff00>green</color>");
                consolePlugin.logMessage(LOG, "", "<color=#00ff007f>green</color>");

                consolePlugin.logMessage(LOG, "", "<color=#0000ff>blue</color>");
                consolePlugin.logMessage(LOG, "", "<color=#0000ff7f>blue</color>");

                consolePlugin.logMessage(LOG, "", "<color=#ff0000>r<i>r<color=#00ff00>g<b>g<color=#0000ff>bb");
                consolePlugin.logMessage(LOG, "", "This is <color=red>red <b>bold <i>ita</i>lic</b> attributed</color> text.");
                consolePlugin.showConsole();
                */
            }
        });

        final Button loggerButton = findViewById(R.id.test_button_start_logger);
        loggerButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (loggerThread == null) {
                    loggerThread = new Thread(new Runnable() {
                        @Override
                        public void run() {
                            try {
                                List<FakeLogEntry> entries = readFakeLogEntries("input.txt");
                                logEntries(entries);
                            } catch (Exception e) {
                                e.printStackTrace();
                            }
                        }

                        private void logEntries(List<FakeLogEntry> entries) {
                            long delay = Integer.parseInt(delayEditText.getText().toString());

                            while (!Thread.currentThread().isInterrupted()) {
                                final FakeLogEntry entry = entries.get(logIndex);
                                logIndex = (logIndex + 1) % entries.size();

                                dispatchOnSelectedQueue(new DispatchTask() {
                                    @Override
                                    protected void execute() {
                                        String stacktrace = isStackTraceEnabled() ? entry.stacktrace : null;
                                        consolePlugin.logMessage(entry.type, stacktrace, entry.message);
                                    }
                                });

                                try {
                                    Thread.sleep(delay);
                                } catch (InterruptedException e) {
                                    break;
                                }
                            }
                        }

                        private List<FakeLogEntry> readFakeLogEntries(String filename) throws IOException, JSONException {
                            List<FakeLogEntry> entries = new ArrayList<>();

                            String jsonText = readTextAsset(filename);
                            JSONArray array = new JSONArray(jsonText);
                            for (int i = 0; i < array.length(); ++i) {
                                JSONObject obj = (JSONObject) array.get(i);
                                byte type = parseType(obj.getString("level"));
                                String message = obj.getString("message");
                                String stackTrace = obj.getString("stacktrace");

                                entries.add(new FakeLogEntry(type, message, stackTrace));
                            }
                            return entries;
                        }
                    });
                    loggerThread.start();
                    loggerButton.setText(R.string.button_logger_stop);
                } else {
                    loggerThread.interrupt();
                    loggerThread = null;
                    loggerButton.setText(R.string.button_logger_start);
                }
            }

            private byte parseType(String type) {
                switch (type) {
                    case "ERROR":
                        return ERROR;
                    case "WARNING":
                        return WARNING;
                }

                return LOG;
            }

            private String readTextAsset(String filename) throws IOException {
                InputStream is = getAssets().open(filename);
                int size = is.available();
                byte[] buffer = new byte[size];
                is.read(buffer);
                is.close();

                return new String(buffer, "UTF-8");
            }
        });

        Button errorButton = findViewById(R.id.test_button_log_exception);
        errorButton.setOnClickListener(v -> dispatchOnSelectedQueue(new DispatchTask() {
            @Override
            protected void execute() {
                consolePlugin.logMessage(EXCEPTION, "UnityEngine.Debug:LogError(Object)\n" +
                        "Test:Method(String) (at /Users/lunar-unity-console/Project/Assets/Scripts/Test.cs:30)\n" +
                        "<LogMessages>c__Iterator0:MoveNext() (at /Users/lunar-unity-console/Project/Assets/Logger.cs:85)\n" +
                        "UnityEngine.MonoBehaviour:StartCoroutine(IEnumerator)\n" +
                        "Logger:LogMessages() (at /Users/lunar-unity-console/Project/Assets/Logger.cs:66)\n" +
                        "UnityEngine.EventSystems.EventSystem:Update()", "Exception is thrown");
            }
        }));

        final Button showConsole = findViewById(R.id.test_button_show_console);
        showConsole.setOnClickListener(v -> openConsole());

        final Button showOverlay = findViewById(R.id.test_button_show_overlay);
        showOverlay.setEnabled(false);
//		showOverlay.setOnClickListener(new View.OnClickListener() {
//			@Override
//			public void onClick(View v) {
//				dispatchOnSelectedQueue(new Runnable() {
//					@Override
//					public void run() {
//						if (consolePlugin.isOverlayShown()) {
//							consolePlugin.hideOverlay();
//						} else {
//							consolePlugin.showOverlay();
//						}
//					}
//				});
//			}
//		});

        setLogOnClickListener(R.id.test_button_log_debug, ConsoleLogType.LOG);
        setLogOnClickListener(R.id.test_button_log_warning, ConsoleLogType.WARNING);
        setLogOnClickListener(R.id.test_button_log_error, ConsoleLogType.ERROR);

//		setOnClickListener(R.id.test_button_set_capacity, new View.OnClickListener() {
//			@Override
//			public void onClick(View v) {
//				EditText capacityEditText = (EditText) findViewById(R.id.test_edit_text_capacity);
//				String capacityText = capacityEditText.getText().toString();
//				int capacity = StringUtils.parseInt(capacityText, 0);
//				if (capacity > 0) {
//					consolePlugin.setCapacity(capacity);
//				} else {
//					Toast.makeText(MainActivity.this, "Invalid capacity: " + capacityText, Toast.LENGTH_SHORT).show();
//				}
//			}
//		});
//
//		setOnClickListener(R.id.test_button_set_trim, new View.OnClickListener() {
//			@Override
//			public void onClick(View v) {
//				EditText trimEditText = (EditText) findViewById(R.id.test_edit_text_trim);
//				String trimText = trimEditText.getText().toString();
//				int trim = StringUtils.parseInt(trimText, 0);
//				if (trim > 0) {
//					ConsolePlugin.setTrimSize(trim);
//				} else {
//					Toast.makeText(MainActivity.this, "Invalid trim: " + trimText, Toast.LENGTH_SHORT).show();
//				}
//			}
//		});
    }

    private String readTextAsset(String filename) {
        try (InputStream stream = getAssets().open(filename)) {
            try (final BufferedReader reader = new BufferedReader(new InputStreamReader(stream))) {
                String line;
                final StringBuilder result = new StringBuilder();
                while ((line = reader.readLine()) != null) {
                    if (result.length() > 0) {
                        result.append('\n');
                    }
                    result.append(line);
                }
                return result.toString();
            }
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        saveUIState();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();

        if (loggerThread != null) {
            loggerThread.interrupt();
            loggerThread = null;
        }

        if (shutdownPluginWhenDestroyed) {
            dispatchOnSelectedQueue(new DispatchTask() {
                @Override
                protected void execute() {
                    consolePlugin.destroy();
                }
            });
        }
    }

    ////////////////////////////////////////////////////////////////////////////////////////////////
    // Threading

    private void dispatchOnSelectedQueue(DispatchTask r) {
        if (forceSyncCalls) {
            r.run();
        } else {
            DispatchQueue queue = shouldUseMainThread() ? mainQueue : backgroundQueue;
            queue.dispatch(r);
        }
    }

    private boolean shouldUseMainThread() {
        return useMainThreadCheckBox.isChecked();
    }

    private boolean isStackTraceEnabled() {
        return enableStackTraceCheckBox.isChecked();
    }

    ////////////////////////////////////////////////////////////////////////////////////////////////
    // UI state

    private void saveUIState() {
        SharedPreferences prefs = getSharedPreferences();
        SharedPreferences.Editor editor = prefs.edit();
        saveState(editor, KEY_TEXT_CAPACITY, capacityEditText);
        saveState(editor, KEY_TEXT_TRIM, trimEditText);
        saveState(editor, KEY_TEXT_DELAY, delayEditText);
        saveState(editor, KEY_CHECKBOX_USE_MAIN_THREAD, useMainThreadCheckBox);
        saveState(editor, KEY_CHECKBOX_ENABLE_STACK_TRACE, enableStackTraceCheckBox);
        editor.apply();
    }

    private void restoreUIState() {
        SharedPreferences prefs = getSharedPreferences();

        loadState(prefs, KEY_TEXT_CAPACITY, capacityEditText);
        loadState(prefs, KEY_TEXT_TRIM, trimEditText);
        loadState(prefs, KEY_TEXT_DELAY, delayEditText);
        loadState(prefs, KEY_CHECKBOX_USE_MAIN_THREAD, useMainThreadCheckBox);
        loadState(prefs, KEY_CHECKBOX_ENABLE_STACK_TRACE, enableStackTraceCheckBox);
    }

    private void saveState(SharedPreferences.Editor editor, String key, EditText editText) {
        editor.putString(key, editText.getText().toString());
    }

    private void saveState(SharedPreferences.Editor editor, String key, CheckBox checkBox) {
        editor.putBoolean(key, checkBox.isChecked());
    }

    private void loadState(SharedPreferences prefs, String key, EditText editText) {
        String text = prefs.getString(key, null);
        if (text != null) {
            editText.setText(text);
        }
    }

    private void loadState(SharedPreferences prefs, String key, CheckBox checkBox) {
        checkBox.setChecked(prefs.getBoolean(key, checkBox.isChecked()));
    }

    private SharedPreferences getSharedPreferences() {
        return getSharedPreferences(TEST_PREFS_NAME, MODE_PRIVATE);
    }

    static void clearSharedPreferences(Context context) {
        SharedPreferences prefs = context.getSharedPreferences(TEST_PREFS_NAME, MODE_PRIVATE);
        SharedPreferences.Editor edit = prefs.edit();
        edit.clear();
        edit.apply();

        // PluginSettings.clear(context); // FIXME
        ConsoleViewState.clear(context);
    }

    ////////////////////////////////////////////////////////////////////////////////////////////////
    // Helpers

    private void setLogOnClickListener(int id, final byte logType) {
        setOnClickListener(id, v -> {
            final EditText messageText = findViewById(R.id.test_edit_message);
            dispatchOnSelectedQueue(new DispatchTask() {
                @Override
                protected void execute() {
                    String message = messageText.getText().toString();
                    consolePlugin.logMessage(logType, "", message);
                }
            });
        });
    }

    private void setOnClickListener(int id, View.OnClickListener listener) {
        findViewById(id).setOnClickListener(listener);
    }

    public void openConsole() {
        dispatchOnSelectedQueue(new DispatchTask() {
            @Override
            protected void execute() {
                consolePlugin.showConsole();
            }
        });
    }

    ////////////////////////////////////////////////////////////////////////////////////////////////
    // Helpers classes

    class FakeLogEntry {
        public final byte type;
        public final String message;
        public final String stacktrace;

        FakeLogEntry(byte type, String message, String stacktrace) {
            this.type = type;
            this.message = message;
            this.stacktrace = stacktrace;
        }
    }
}
