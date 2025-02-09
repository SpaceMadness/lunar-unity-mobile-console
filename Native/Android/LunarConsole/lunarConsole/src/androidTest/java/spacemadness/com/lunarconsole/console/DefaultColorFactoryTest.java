//
//  DefaultColorFactoryTest.java
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

import androidx.test.platform.app.InstrumentationRegistry;

import org.junit.Test;

import static org.junit.Assert.assertEquals;

public class DefaultColorFactoryTest {
    @Test
    public void testBuiltinColors() {
        ColorFactory factory = new DefaultColorFactory(
                InstrumentationRegistry.getInstrumentation().getTargetContext()
        );
        assertEquals(0xffff00ff, factory.fromValue("error"));
        assertEquals(0xff00ffff, factory.fromValue("aqua"));
        assertEquals(0xff000000, factory.fromValue("black"));
        assertEquals(0xff0000ff, factory.fromValue("blue"));
        assertEquals(0xffa52a2a, factory.fromValue("brown"));
        assertEquals(0xff00ffff, factory.fromValue("cyan"));
        assertEquals(0xff0000a0, factory.fromValue("darkblue"));
        assertEquals(0xffff00ff, factory.fromValue("fuchsia"));
        assertEquals(0xff008000, factory.fromValue("green"));
        assertEquals(0xff808080, factory.fromValue("grey"));
        assertEquals(0xffadd8e6, factory.fromValue("lightblue"));
        assertEquals(0xff00ff00, factory.fromValue("lime"));
        assertEquals(0xffff00ff, factory.fromValue("magenta"));
        assertEquals(0xff800000, factory.fromValue("maroon"));
        assertEquals(0xff000080, factory.fromValue("navy"));
        assertEquals(0xff808000, factory.fromValue("olive"));
        assertEquals(0xffffa500, factory.fromValue("orange"));
        assertEquals(0xff800080, factory.fromValue("purple"));
        assertEquals(0xffff0000, factory.fromValue("red"));
        assertEquals(0xffc0c0c0, factory.fromValue("silver"));
        assertEquals(0xff008080, factory.fromValue("teal"));
        assertEquals(0xffffffff, factory.fromValue("white"));
        assertEquals(0xffffff00, factory.fromValue("yellow"));
    }

    @Test
    public void testBuiltinColorsCaseInsensitive() {
        ColorFactory factory = new DefaultColorFactory(
                InstrumentationRegistry.getInstrumentation().getTargetContext()
        );
        assertEquals(0xff00ffff, factory.fromValue("AqUA"));
    }

    @Test
    public void testParseColors() {
        ColorFactory factory = new DefaultColorFactory(
                InstrumentationRegistry.getInstrumentation().getTargetContext()
        );
        assertEquals(0xffabcdef, factory.fromValue("#abcdef"));
        assertEquals(0xffabcdef, factory.fromValue("#ABCDEF"));
        assertEquals(0xffabcdef, factory.fromValue("#ABCDEF7f"));
    }

    @Test
    public void testParseInvalidColors() {
        ColorFactory factory = new DefaultColorFactory(
                InstrumentationRegistry.getInstrumentation().getTargetContext()
        );
        assertEquals(0xffff00ff, factory.fromValue("foo"));
        assertEquals(0xffff00ff, factory.fromValue("#xyz"));
    }
}
