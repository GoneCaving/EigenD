/*
 Copyright 2009 Eigenlabs Ltd.  http://www.eigenlabs.com

 This file is part of EigenD.

 EigenD is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 EigenD is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with EigenD.  If not, see <http://www.gnu.org/licenses/>.
*/

#ifndef __CONTROL_MAPPING__
#define __CONTROL_MAPPING__

#include <midilib_exports.h>

#include <piw/piw_tsd.h>
#include <picross/pic_functor.h>

#define GLOBAL_SCOPE 0
#define PERNOTE_SCOPE 1
#define CHANNEL_SCOPE 2

#define BITS_7 7
#define BITS_14 14

#define CURVE_LINEAR 0
#define CURVE_CUBIC 1
#define CURVE_QUADRATIC 2
#define CURVE_STEP 3

namespace midi
{
    class MIDILIB_DECLSPEC_CLASS mapping_observer_t: virtual public pic::tracked_t
    {
        public:
            virtual ~mapping_observer_t() { tracked_invalidate(); };

            virtual void mapping_changed(const std::string &) = 0;
            virtual void parameter_changed(unsigned) = 0;
            virtual void settings_changed() = 0;
            virtual std::string get_parameter_name(unsigned i) = 0;
    };

    struct MIDILIB_DECLSPEC_CLASS global_settings_t
    {
        global_settings_t(const global_settings_t &g): midi_channel_(g.midi_channel_), minimum_midi_channel_(g.minimum_midi_channel_), maximum_midi_channel_(g.maximum_midi_channel_), minimum_decimation_(g.minimum_decimation_), send_notes_(g.send_notes_), send_pitchbend_(g.send_pitchbend_), send_hires_velocity_(g.send_hires_velocity_), pitchbend_semitones_up_(g.pitchbend_semitones_up_), pitchbend_semitones_down_(g.pitchbend_semitones_down_)  {};
        global_settings_t(): midi_channel_(0), minimum_midi_channel_(1), maximum_midi_channel_(16), minimum_decimation_(0.f), send_notes_(true), send_pitchbend_(true), send_hires_velocity_(false), pitchbend_semitones_up_(1.0f), pitchbend_semitones_down_(1.0f) {};
        global_settings_t(unsigned midi_channel, unsigned minimum_midi_channel, unsigned maximum_midi_channel, float minimum_decimation, bool send_notes, bool send_pitchbend, bool send_hires_velocity, float pb_up, float pb_down): midi_channel_(midi_channel), minimum_midi_channel_(minimum_midi_channel), maximum_midi_channel_(maximum_midi_channel), minimum_decimation_(minimum_decimation), send_notes_(send_notes), send_pitchbend_(send_pitchbend), send_hires_velocity_(send_hires_velocity), pitchbend_semitones_up_(pb_up), pitchbend_semitones_down_(pb_down)  {};

        global_settings_t clone_with_midi_channel(unsigned);
        global_settings_t clone_with_minimum_midi_channel(unsigned);
        global_settings_t clone_with_maximum_midi_channel(unsigned);
        global_settings_t clone_with_minimum_decimation(float);
        global_settings_t clone_with_send_notes(bool);
        global_settings_t clone_with_send_pitchbend(bool);
        global_settings_t clone_with_send_hires_velocity(bool);
        global_settings_t clone_with_pitchbend_semitones_up(float);
        global_settings_t clone_with_pitchbend_semitones_down(float);

        unsigned get_midi_channel() { return midi_channel_; }
        unsigned get_minimum_midi_channel() { return minimum_midi_channel_; }
        unsigned get_maximum_midi_channel() { return maximum_midi_channel_; }
        float get_minimum_decimation() { return minimum_decimation_; }
        bool get_send_notes() { return send_notes_; }
        bool get_send_pitchbend() { return send_pitchbend_; }
        bool get_send_hires_velocity() { return send_hires_velocity_; }
        float get_pitchbend_semitones_up() { return pitchbend_semitones_up_; }
        float get_pitchbend_semitones_down() { return pitchbend_semitones_down_; }

        bool operator==(const global_settings_t &) const;

        unsigned midi_channel_;
        unsigned minimum_midi_channel_;
        unsigned maximum_midi_channel_;
        float minimum_decimation_;
        bool send_notes_;
        bool send_pitchbend_;
        bool send_hires_velocity_;
        float pitchbend_semitones_up_;
        float pitchbend_semitones_down_;
    };

    struct MIDILIB_DECLSPEC_CLASS mapping_data_t
    {
        mapping_data_t(): scale_(0.f), lo_(0.f), base_(0.f), hi_(1.f), origin_return_(false), decimation_(0.f), scope_(GLOBAL_SCOPE), channel_(0), resolution_(BITS_7), secondary_cc_(-1), curve_(CURVE_LINEAR) {};
        mapping_data_t(float scale, float lo, float base, float hi, bool origin_return, float decimation, unsigned scope, unsigned channel, unsigned resolution, int secondary, unsigned curve): scale_(scale), lo_(lo), base_(base), hi_(hi), origin_return_(origin_return), decimation_(decimation), scope_(scope), channel_(channel), resolution_(resolution), secondary_cc_(secondary), curve_(curve) {};

        float calculate(float norm_data) const;

        float scale_;
        float lo_;
        float base_;
        float hi_;
        bool origin_return_;
        float decimation_;
        unsigned scope_;
        unsigned channel_;
        unsigned resolution_;
        int secondary_cc_; 
        unsigned curve_; 
    };

    class MIDILIB_DECLSPEC_CLASS decimation_handler_t;

    class MIDILIB_DECLSPEC_CLASS mapping_wrapper_t: public mapping_data_t
    {
        public:
            mapping_wrapper_t(bool decimate_per_id, float scale, float lo, float base, float hi, bool origin_return, float decimation, unsigned scope, unsigned channel, unsigned resolution, int secondary, unsigned curve);
            mapping_wrapper_t(const mapping_wrapper_t &o);
            ~mapping_wrapper_t();

            bool valid_for_processing(const piw::data_nb_t &id, unsigned long long current_time);
            void done_processing(const piw::data_nb_t &id);

        private:
            decimation_handler_t * const decimation_handler_;
    };

    class controllers_mapping_t;

    typedef pic::lckmap_t<unsigned,mapping_wrapper_t>::nbtype nb_param_map_t;
    typedef pic::lckmap_t<unsigned,float>::nbtype nb_origin_map_t;
    typedef pic::lckmap_t<unsigned,mapping_wrapper_t>::nbtype nb_midi_map_t;

    class MIDILIB_DECLSPEC_CLASS control_mapping_t
    {
        public:
            control_mapping_t(unsigned name) : name_(name), mapping_serial_(0), origins_update_(0) {};
            unsigned name() { return name_; }
            void reset_serial() { mapping_serial_ = 0; };
            void touch_origins_update() { origins_update_ = piw::tsd_time(); };
            nb_param_map_t &params() { return params_; };
            nb_origin_map_t &origins() { return origins_; };
            nb_midi_map_t &midi() { return midi_; };

        private:
            friend class controllers_mapping_t;

            unsigned name_;
            nb_param_map_t params_;
            nb_origin_map_t origins_;
            nb_midi_map_t midi_;
            global_settings_t settings_;
            unsigned mapping_serial_;
            unsigned long long origins_update_;
    };

    struct MIDILIB_DECLSPEC_CLASS mapping_info_t: public mapping_data_t
    {
        mapping_info_t(): oparam_(-1), enabled_(true) {};
        mapping_info_t(unsigned short oparam): mapping_data_t(1.f, 0.f, 0.f, 1.f, false, 0.f, GLOBAL_SCOPE, 0, BITS_7, -1, CURVE_LINEAR), oparam_(oparam), enabled_(true) {};
        mapping_info_t(const mapping_info_t &i): mapping_data_t(i.scale_, i.lo_, i.base_, i.hi_, i.origin_return_, i.decimation_, i.scope_, i.channel_, i.resolution_, i.secondary_cc_, i.curve_), oparam_(i.oparam_), enabled_(i.enabled_) {};
        mapping_info_t(unsigned short oparam, bool enabled, float scale, float lo, float base, float hi, bool origin_return, float decimation, unsigned scope, unsigned channel, unsigned resolution, int secondary, unsigned curve): mapping_data_t(scale, lo, base, hi, origin_return, decimation, scope, channel, resolution, secondary, curve), oparam_(oparam), enabled_(enabled) {};

        mapping_info_t clone_with_enabled(bool);
        mapping_info_t clone_with_scale(float);
        mapping_info_t clone_with_lo(float);
        mapping_info_t clone_with_base(float);
        mapping_info_t clone_with_hi(float);
        mapping_info_t clone_with_origin_return(bool);
        mapping_info_t clone_with_decimation(float);
        mapping_info_t clone_with_scope(unsigned);
        mapping_info_t clone_with_channelscope(unsigned);
        mapping_info_t clone_with_resolution(unsigned);
        mapping_info_t clone_with_secondarycc(int);
        mapping_info_t clone_with_curve(unsigned);

        int oparam_;
        bool enabled_;

        bool is_valid() const { return oparam_>=0 && scale_!=0.0; }
    };

    typedef pic::lckmultimap_t<unsigned,mapping_info_t>::lcktype control_map_t;
    typedef std::pair<control_map_t::const_iterator,control_map_t::const_iterator> controllers_map_range_t;

    class MIDILIB_DECLSPEC_CLASS controllers_mapping_t: public pic::guarded_t, virtual public pic::tracked_t
    {
        public:
            controllers_mapping_t(mapping_observer_t &l) : listener_(l), acquired_(0) {};

            unsigned get_serial();

            void set_mapping(const std::string &);
            std::string get_mapping();
            void map_param(unsigned, mapping_info_t &);
            void map_midi(unsigned, mapping_info_t &);
            void unmap_param(unsigned, unsigned short);
            void unmap_midi(unsigned, unsigned short);
            bool is_mapped_param(unsigned, unsigned short);
            bool is_mapped_midi(unsigned, unsigned short);
            mapping_info_t get_info_param(unsigned, unsigned short);
            mapping_info_t get_info_midi(unsigned, unsigned short);
            void clear_params();
            void clear_midi_cc();
            void clear_midi_behaviour();
            global_settings_t get_settings();
            void change_settings(global_settings_t);
            void settings_changed();

            controllers_map_range_t param_mappings(unsigned);
            controllers_map_range_t midi_mappings(unsigned);

            void refresh_mappings(control_mapping_t &);
            void refresh_params(control_mapping_t &);
            void refresh_origins(control_mapping_t &, pic::i2f_t);
            void refresh_midi(control_mapping_t &);

            void acquire();
            void release();

        private:
            void map(control_map_t &, unsigned, mapping_info_t);
            void unmap(control_map_t &, unsigned, unsigned short);
            bool is_mapped(const control_map_t &, unsigned, unsigned short);
            mapping_info_t get_info(const control_map_t &, unsigned, unsigned short);
            void unmap_span_overlaps(unsigned, int);

            void refresh_params_(control_mapping_t &);
            void refresh_origins_(control_mapping_t &, pic::i2f_t &);
            void refresh_midi_(control_mapping_t &);

            struct MIDILIB_DECLSPEC_CLASS mapping_t
            {
                control_map_t map_params_;
                control_map_t map_midi_;
                global_settings_t settings_;
                unsigned serial_;
            };

            mapping_observer_t &listener_;
            pic::flipflop_t<mapping_t> mapping_;
            const mapping_t* acquired_;
    };

}; // namespace midi


#endif /* __CONTROL_MAPPING__ */
