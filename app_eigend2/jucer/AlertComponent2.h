/*
  ==============================================================================

  This is an automatically generated file created by the Jucer!

  Creation date:  24 Sep 2012 6:35:44pm

  Be careful when adding custom code to these files, as only the code within
  the "//[xyz]" and "//[/xyz]" sections will be retained when the file is loaded
  and re-saved.

  Jucer version: 1.12

  ------------------------------------------------------------------------------

  The Jucer is part of the JUCE library - "Jules' Utility Class Extensions"
  Copyright 2004-6 by Raw Material Software ltd.

  ==============================================================================
*/

#ifndef __JUCER_HEADER_ALERTCOMPONENT_ALERTCOMPONENT_C8B655__
#define __JUCER_HEADER_ALERTCOMPONENT_ALERTCOMPONENT_C8B655__

//[Headers]     -- You can add your own extra header files here --
#include "juce.h"
//[/Headers]



//==============================================================================
/**
                                                                    //[Comments]
    An auto-generated component, created by the Jucer.

    Describe your class and how it works here!
                                                                    //[/Comments]
*/
class AlertComponent2  : public Component,
                         public Button::Listener
{
public:
    //==============================================================================
    AlertComponent2 ();
    ~AlertComponent2();

    //==============================================================================
    //[UserMethods]     -- You can add your own custom methods in this section.
    void set_title(const String &t) { title->setText(t,dontSendNotification); }
    void set_text(const String &t) { text->setText(t,dontSendNotification); }
    Button *get_ok_button() { return ok_button; }
    Button *get_cancel_button() { return cancel_button; }
    ToggleButton *get_toggle_button() { return toggleButton; }
    //[/UserMethods]

    void paint (Graphics& g);
    void resized();
    void buttonClicked (Button* buttonThatWasClicked);

    // Binary resources:
    static const char* backgroundBoxT_png;
    static const int backgroundBoxT_pngSize;
    static const char* backgroundBoxL_png;
    static const int backgroundBoxL_pngSize;
    static const char* backgroundBoxR_png;
    static const int backgroundBoxR_pngSize;
    static const char* backgroundBoxB_png;
    static const int backgroundBoxB_pngSize;
    static const char* backgroundBoxTl_png;
    static const int backgroundBoxTl_pngSize;
    static const char* backgroundBoxTr_png;
    static const int backgroundBoxTr_pngSize;
    static const char* backgroundBoxBl_png;
    static const int backgroundBoxBl_pngSize;
    static const char* backgroundBoxBr_png;
    static const int backgroundBoxBr_pngSize;
    static const char* backgroundBoxInner_png;
    static const int backgroundBoxInner_pngSize;
    static const char* eigenD_png;
    static const int eigenD_pngSize;


private:
    //[UserVariables]   -- You can add your own custom variables in this section.
    //[/UserVariables]

    //==============================================================================
    ToggleButton* toggleButton;
    Label* title;
    TextButton* ok_button;
    TextButton* cancel_button;
    Label* text;
    Image cachedImage_backgroundBoxInner_png;
    Image cachedImage_backgroundBoxT_png;
    Image cachedImage_backgroundBoxL_png;
    Image cachedImage_backgroundBoxR_png;
    Image cachedImage_backgroundBoxTl_png;
    Image cachedImage_backgroundBoxTr_png;
    Image cachedImage_backgroundBoxB_png;
    Image cachedImage_backgroundBoxBr_png;
    Image cachedImage_backgroundBoxBl_png;
    Image cachedImage_eigenD_png;


    //==============================================================================
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (AlertComponent2);
};


#endif   // __JUCER_HEADER_ALERTCOMPONENT_ALERTCOMPONENT_C8B655__
