//
//  InstrumentationTestCase.java
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

package spacemadness.com.lunarconsole;

import android.content.Context;

import androidx.test.platform.app.InstrumentationRegistry;

import junit.framework.TestCase;

import java.io.IOException;

public class InstrumentationTestCase extends TestCase {
    protected String readTextAsset(String path) {
        try {
            return TestUtils.readTextAsset(getContext(), path);
        } catch (IOException e) {
            throw new AssertionError("Unable to read text asset: " + path, e);
        }
    }

    private Context getContext() {
        return InstrumentationRegistry.getInstrumentation().getContext();
    }
}
