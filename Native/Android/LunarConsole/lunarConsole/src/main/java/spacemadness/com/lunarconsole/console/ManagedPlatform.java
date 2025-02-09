//
//  ManagedPlatform.java
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


package spacemadness.com.lunarconsole.console;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.view.View;
import android.view.ViewGroup;

import com.unity3d.player.UnityPlayer;

import java.lang.ref.WeakReference;
import java.lang.reflect.Field;
import java.util.Map;

import spacemadness.com.lunarconsole.debug.Log;
import spacemadness.com.lunarconsole.utils.UIUtils;

import static spacemadness.com.lunarconsole.debug.Tags.PLUGIN;

import androidx.annotation.Nullable;

public class ManagedPlatform implements Platform {
    private final UnityScriptMessenger scriptMessenger;
    private final WeakReference<Activity> activity;

    public ManagedPlatform(Activity activity, String target, String method) {
        this.activity = new WeakReference<>(activity);
        scriptMessenger = new UnityScriptMessenger(target, method);
    }

    @Override
    public View getTouchRecipientView() {
        Activity currentActivity = activity.get();
        if (currentActivity == null) {
            Log.e(PLUGIN, "UnityPlayer.currentActivity is null");
            return null;

        }

        UnityPlayer unityPlayer = resolveUnityPlayer(currentActivity);
        if (unityPlayer == null) {
            Log.e(PLUGIN, "UnityPlayer instance is null");
            return null;
        }


        // Cast to Object first to handle newer Unity versions where UnityPlayer may not extend View.
        // This avoids compilation errors while maintaining compatibility with older versions.
        Object unityPlayerObject = unityPlayer;
        if (unityPlayerObject instanceof View) {
            return (View) unityPlayerObject;
        }

        return unityPlayer.getFrameLayout();
    }

    @Override
    public void sendUnityScriptMessage(String name, Map<String, Object> data) {
        try {
            scriptMessenger.sendMessage(name, data);
        } catch (Exception e) {
            Log.e(PLUGIN, "Error while sending Unity script message: name=%s param=%s", name, data);
        }
    }

    /**
     * Attempts to resolve the UnityPlayer instance using multiple strategies.
     * First tries reflection, then falls back to UI hierarchy search.
     *
     * @param activity The current activity
     * @return The UnityPlayer instance if found, null otherwise
     */
    @Nullable
    private static UnityPlayer resolveUnityPlayer(Activity activity) {
        UnityPlayer unityPlayer = resolveUnityPlayerWithReflection(activity);
        if (unityPlayer != null) {
            return unityPlayer;
        }
        return resolveUnityPlayerUiSearch(activity);
    }

    /**
     * Attempts to resolve the UnityPlayer instance using reflection.
     * Looks for the mUnityPlayer field in the activity class.
     *
     * @param activity The current activity
     * @return The UnityPlayer instance if found through reflection, null otherwise
     */
    @Nullable
    private static UnityPlayer resolveUnityPlayerWithReflection(Activity activity) {
        try {
            @SuppressLint("PrivateApi")
            Field unityPlayerField = activity.getClass().getDeclaredField("mUnityPlayer");
            unityPlayerField.setAccessible(true);
            Object fieldValue = unityPlayerField.get(activity);
            if (fieldValue instanceof UnityPlayer) {
                return (UnityPlayer) fieldValue;
            } else {
                Log.e(PLUGIN, "Unable to resolve Unity player: mUnityPlayer field is not of type UnityPlayer");
            }
        } catch (NoSuchFieldException e) {
            Log.e(PLUGIN, "Unable to resolve Unity player: could not find mUnityPlayer field: %s", e);
        } catch (IllegalAccessException e) {
            Log.e(PLUGIN, "Unable to resolve Unity player: could not access mUnityPlayer field: %s", e);
        } catch (Exception e) {
            Log.e(PLUGIN, "Unable to resolve Unity player: unexpected error while getting UnityPlayer instance: %s", e);
        }
        return null;
    }

    /**
     * Initiates a UI hierarchy search for the UnityPlayer instance starting from the activity's root view.
     *
     * @param activity The current activity
     * @return The UnityPlayer instance if found in the UI hierarchy, null otherwise
     */
    private static UnityPlayer resolveUnityPlayerUiSearch(Activity activity) {
        return resolveUnityPlayerUiSearch(UIUtils.getRootViewGroup(activity));
    }

    /**
     * Recursively searches through the view hierarchy to find the UnityPlayer instance.
     *
     * @param root The root ViewGroup to start the search from
     * @return The UnityPlayer instance if found in the view hierarchy, null otherwise
     */
    private static UnityPlayer resolveUnityPlayerUiSearch(ViewGroup root) {
        // Cast to Object for binary compatibility with different Unity versions.
        // In some older Unity versions, UnityPlayer extends View class.
        // In other newer Unity versions, UnityPlayer no longer extends View, so we need to use Object
        // to avoid compilation errors while maintaining runtime compatibility.
        Object rootObject = root;

        if (rootObject instanceof UnityPlayer) {
            return (UnityPlayer) rootObject;
        }

        for (int i = 0; i < root.getChildCount(); ++i) {
            // Same binary compatibility approach for child views.
            Object child = root.getChildAt(i);
            if (child instanceof UnityPlayer) {
                return (UnityPlayer) child;
            }

            if (child instanceof ViewGroup) {
                UnityPlayer player = resolveUnityPlayerUiSearch((ViewGroup) child);
                if (player != null) {
                    return player;
                }
            }
        }

        return null;
    }
}