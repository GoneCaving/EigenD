
#
# Copyright 2009 Eigenlabs Ltd.  http://www.eigenlabs.com
#
# This file is part of EigenD.
#
# EigenD is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# EigenD is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EigenD.  If not, see <http://www.gnu.org/licenses/>.
#

from pi import agent,atom,action,bundles,domain,errors,paths,policy,async,logic,const,node,upgrade,utils,container,timeout,paths,guid
from . import keygroup_version as version
from pi.logic.shortcuts import *
import piw
import picross

def removelist(l1,s):
    l2=[]
    for l in l1:
        if l not in s:
            l2.append(l)
    return l2


class SlowTonicChange:
    def __init__(self,agent,tonic):
        self.__agent = agent
        self.__tonic = tonic

    def change(self,d):
        if d.as_norm() != 0:
            self.__agent[19].set_value(self.__tonic)


class SlowScaleChange:
    def __init__(self,agent,scale):
        self.__agent = agent
        self.__scale = scale 

    def change(self,d):
        if d.as_norm() != 0:
            self.__agent[20].set_value(self.__scale)


class Controller:
    def __init__(self,agent,cookie):
        self.__agent = agent
        self.__dict = piw.controllerdict(cookie)
        self.__state = node.Server(change=self.__change_controller)

    def changetonic(self,t):
        return self.__dict.changetonic(t)

    def changescale(self,s):
        return self.__dict.changescale(s)

    def state(self):
        return self.__state

    def __change_controller(self,d):
        if d.is_dict():
            for x in ('courseoffset','courselen','columnoffset','columnlen'):
                v = d.as_dict_lookup(x)
                self.__dict.put_ctl(x,v)
            self.__state.set_data(self.__dict.get_ctl_dict().make_normal())

    def thing_changed(self,d,kk):
        self.__dict.put(kk,d)

    def set_course_semis(self,idx,val):
        self.ensure(idx)
        l = [i.as_float() for i in self.getlist('courseoffset')]
        l[idx-1] = float(val+10000 if val else 0)
        self.setlist('courseoffset',[piw.makefloat(i,0) for i in l])

    def set_course_steps(self,idx,val):
        self.ensure(idx)
        l = [i.as_float() for i in self.getlist('courseoffset')]
        l[idx-1] = float(val)
        self.setlist('courseoffset',[piw.makefloat(i,0) for i in l])

    def get_course_lengths(self):
        l = [i.as_long() for i in self.getlist('courselen')]
        c = []
        i = 0
        while i < len(l):
           c.append(l[i]) 
           i = i + 1
        return tuple(c)

    def set_course_lengths(self,courses):
        lengths = []
        for l in courses:
            offsets.append(piw.makelong(l,0))
        self.setlist('courselen',lengths)

    def get_course_offsets(self):
        o = [i.as_float() for i in self.getlist('courseoffset')]
        c = []
        i = 0
        while i < len(o):
           c.append(o[i]) 
           i = i + 1
        return tuple(c)

    def set_course_offsets(self,courses):
        offsets = []
        for o in courses:
            offsets.append(piw.makefloat(o,0))
        self.setlist('courseoffset',offsets)

    def num_courses(self):
        l = self.getlist('courseoffset')
        return len(l) if l else 0

    def update_labels(self):
        labels = None

        category = self.__agent[38].get_value()
        label = self.__agent[39].get_value()
        if label is None or 0 == len(label):
            label = self.__agent.get_description()
        if category and len(category) > 0:
            if self.__agent.upstream_labels is None:
                labels = []
            else:
                labels = list(self.__agent.upstream_labels)
            labels.append(utils.maketuple([piw.makestring(category,0), piw.makestring(label,0)],0))

        if labels is None:
            self.setlist('labels',piw.makenull(0))
        else:
            self.setlist('labels',labels)

    def ensure(self,course):
        l = [i.as_float() for i in self.getlist('courseoffset')]
        if course>len(l):
            xl = course-len(l)
            l.extend([0]*xl)
            self.setlist('courseoffset',[piw.makefloat(i,0) for i in l])

        l = [i.as_long() for i in self.getlist('courselen')]
        if course>len(l):
            xl = course-len(l)
            l.extend([0]*xl)
            self.setlist('courselen',[piw.makelong(i,0) for i in l])

    def setlist(self,name,l):
        self.__dict.put_ctl(name, utils.maketuple(l,piw.tsd_time()))
        self.__state.set_data(self.__dict.get_ctl_dict())

    def settuple(self,name,t):
        self.__dict.put_ctl(name, t)
        self.__state.set_data(self.__dict.get_ctl_dict())

    def getlist(self,name):
        d = self.gettuple(name)
        if d is None or not d.is_tuple():
            return []
        return utils.tuple_items(d)

    def gettuple(self,name):
        d = self.__dict.get_ctl_value(name)
        if d is None or not d.is_tuple():
            return piw.tuplenull(piw.tsd_time())
        return d;
        

class VirtualKey(atom.Atom):
    def __init__(self,size,chosen):
        atom.Atom.__init__(self,names='key',protocols='virtual')
        self.__size=size
        self.__chosen=chosen

    def __key(self,*keys):
        x=','.join(['cmp([dsc(~(a)"#1","%(k)d"),dsc(~(a)"#2","%(k)d"),dsc(~(a)"#3","%(k)d"),dsc(~(a)"#4","%(k)d"),dsc(~(a)"#8","%(k)d")])' % dict(k=k) for k in keys])
        return '[%s]' % x

    def rpc_resolve(self,arg):
        (a,o) = logic.parse_clause(arg)
        if not a and o is None: return self.__key(*range(1,1+self.__size()))
        if a==('chosen',) and o is None: return self.__key(*self.__chosen())
        if a or o is None: return '[]'
        o=int(o)
        if o<1 or o>self.__size(): return '[]'
        return self.__key(o)


class VirtualCourse(atom.Atom):
    def __init__(self,controller):
        self.__controller = controller
        atom.Atom.__init__(self,names='course',protocols='virtual')

    def rpc_resolve(self,arg):
        (a,o) = logic.parse_clause(arg)
        if a or o is None: return '[]'
        o=int(o)
        if o<1 or o>self.__controller.num_courses(): return '[]'
        return '[ideal([~server,course],%d)]'%o


class Output(atom.Atom):
    def __init__(self,master,slot):
        self.__agent = master.agent
        self.__list = master
        self.__slot = slot
        self.__tee = None

        atom.Atom.__init__(self,names='keygroup output',protocols='remove',container=const.verb_node,ordinal=slot)

        self.light_output = piw.clone(True)
        self.light_input = bundles.VectorInput(self.light_output.cookie(),self.__agent.domain,signals=(1,))

        self[2] = bundles.Output(2,False, names='pressure output')
        self[3] = bundles.Output(3,False, names='roll output')
        self[4] = bundles.Output(4,False, names='yaw output')
        self[22] = bundles.Output(5,False, names='key output')
        self[5] = bundles.Output(1,False, names='strip position output',ordinal=1)
        self[9] = bundles.Output(1,False, names='strip position output',ordinal=2)
        self[6] = bundles.Output(1,False, names='breath output')
        self[7] = bundles.Output(1,False, names='controller output', continuous=True)
        self[8] = atom.Atom(names='light input',protocols='revconnect',policy=self.light_input.vector_policy(1,False,clocked=False,auto_slot=True),domain=domain.Aniso())
        self[10] = bundles.Output(2,False, names='absolute strip output',ordinal=1)
        self[11] = bundles.Output(2,False, names='absolute strip output',ordinal=2)
        self[30] = bundles.Output(1,False,names='pedal output', ordinal=1, protocols='')
        self[31] = bundles.Output(1,False,names='pedal output', ordinal=2, protocols='')
        self[32] = bundles.Output(1,False,names='pedal output', ordinal=3, protocols='')
        self[33] = bundles.Output(1,False,names='pedal output', ordinal=4, protocols='')

        self[20] = VirtualKey(self.__agent.keygroup_size,self.__agent.key_choice)

        self[23] = atom.Atom(domain=domain.Bool(),init=False,policy=atom.default_policy(self.enable),names='enable',protocols='set',container=(None,'output%d'%self.__slot,self.__agent.verb_container()))
        self[24] = atom.Atom(domain=domain.BoundedInt(-32767,32767), names='key column', init=None, policy=atom.default_policy(self.__change_key_column))
        self[25] = atom.Atom(domain=domain.BoundedInt(-32767,32767), names='key row', init=None, policy=atom.default_policy(self.__change_key_row))
        self[26] = atom.Atom(domain=domain.Bool(),names='key column end relative',init=False,policy=atom.default_policy(self.__change_key_column_endrel))
        self[27] = atom.Atom(domain=domain.Bool(),names='key row end relative',init=False,policy=atom.default_policy(self.__change_key_row_endrel))

        self[23].add_verb2(1,'set([toggle],~a,role(None,[instance(~self)]))', callback=self.__enable_toggle, status_action=self.__status)
        self[23].add_verb2(2,'set([],~a,role(None,[instance(~s)]))', callback=self.__enable_set, status_action=self.__status)
        self[23].add_verb2(3,'set([un],~a,role(None,[instance(~s)]))', callback=self.__enable_unset, status_action=self.__status)

        self.koutput = bundles.Splitter(self.__agent.domain,self[2],self[3],self[4],self[22])
        self.s1output = bundles.Splitter(self.__agent.domain,self[5],self[10])
        self.s2output = bundles.Splitter(self.__agent.domain,self[9],self[11])
        self.boutput = bundles.Splitter(self.__agent.domain,self[6])
        self.coutput = bundles.Splitter(self.__agent.domain,self[7])
        self.output_pedal1 = bundles.Splitter(self.__agent.domain,self[30])
        self.output_pedal2 = bundles.Splitter(self.__agent.domain,self[31])
        self.output_pedal3 = bundles.Splitter(self.__agent.domain,self[32])
        self.output_pedal4 = bundles.Splitter(self.__agent.domain,self[33])

        self.kpolyctl = piw.polyctl(10,self.koutput.cookie(),False,5)

    def __change_key_column(self,val):
        self[24].set_value(val)
        self.update_status_index()
        return False

    def __change_key_row(self,val):
        self[25].set_value(val)
        self.update_status_index()
        return False

    def __change_key_column_endrel(self,val):
        self[26].set_value(val)
        self.update_status_index()
        return False

    def __change_key_row_endrel(self,val):
        self[27].set_value(val)
        self.update_status_index()
        return False

    def __setstate(self,data):
        state = (data.as_norm()!=0.0)
        self[23].set_value(state)
        self.__set_status(state)

    def enable(self,val):
        self.__agent.mode_selector.select(self.__slot,val)
        return True
    
    def __enable_toggle(self,subj,prop):
        self.enable(not self[23].get_value())
        return action.nosync_return()
    
    def __enable_set(self,subj,prop):
        self.enable(True)
        return action.nosync_return()
    
    def __enable_unset(self,subj,prop):
        self.enable(False)
        return action.nosync_return()

    def __status(self,subj,prop):
        return 'dsc(~(a)"#36","%s")' % self.__slot

    def __set_status(self,active):
        self.__agent.status_lights.set_status(self.__slot,const.status_active if active else const.status_inactive)

    def plumb(self):
        self.unplumb()

        tee = piw.changelist_nb()
        self.__tee = tee

        n = self.__slot

        piw.changelist_connect_nb(tee,self.__agent.kclone.gate(n))
        piw.changelist_connect_nb(tee,self.__agent.s1clone.gate(n))
        piw.changelist_connect_nb(tee,self.__agent.s2clone.gate(n))
        piw.changelist_connect_nb(tee,self.__agent.bclone.gate(n))
        piw.changelist_connect_nb(tee,self.__agent.pedal1_clone.gate(n))
        piw.changelist_connect_nb(tee,self.__agent.pedal2_clone.gate(n))
        piw.changelist_connect_nb(tee,self.__agent.pedal3_clone.gate(n))
        piw.changelist_connect_nb(tee,self.__agent.pedal4_clone.gate(n))

        self.__agent.kclone.set_output(n,self.kpolyctl.cookie())
        self.__agent.s1clone.set_output(n,self.s1output.cookie())
        self.__agent.s2clone.set_output(n,self.s2output.cookie())
        self.__agent.bclone.set_output(n,self.boutput.cookie())
        self.__agent.cclone.set_output(n,self.coutput.cookie())
        self.__agent.pedal1_clone.set_output(n,self.output_pedal1.cookie())
        self.__agent.pedal2_clone.set_output(n,self.output_pedal2.cookie())
        self.__agent.pedal3_clone.set_output(n,self.output_pedal3.cookie())
        self.__agent.pedal4_clone.set_output(n,self.output_pedal4.cookie())

        self.light_output.set_output(1,self.__agent.light_switch.get_input(n))

        self.__agent.mode_selector.gate_output(n,tee,utils.make_change_nb(piw.slowchange(utils.changify(self.__setstate))))
        self.__agent.mode_selector.select(n,self[23].get_value())

    def unplumb(self):
        if self.__tee is not None:
            n = self.__slot
            piw.fastchange(self.__tee)(piw.makebool(False,0))
            self.__agent.mode_selector.clear_output(n)
            self.__agent.kclone.clear_output(n)
            self.__agent.s1clone.clear_output(n)
            self.__agent.s2clone.clear_output(n)
            self.__agent.bclone.clear_output(n)
            self.__agent.cclone.clear_output(n)
            self.__agent.pedal1_clone.clear_output(n)
            self.__agent.pedal2_clone.clear_output(n)
            self.__agent.pedal3_clone.clear_output(n)
            self.__agent.pedal4_clone.clear_output(n)
            self.light_output.clear_output(1)
            
            self.__tee = None
    
    def key_coordinate(self):
        return piw.coordinate(self[24].get_value(),self[25].get_value(),self[26].get_value(),self[27].get_value())

    def update_status_index(self):
        self.__agent.mode_selector.gate_status_coordinate(self.__slot,self.key_coordinate())
        

class OutputList(atom.Atom):
    def __init__(self,agent):
        self.agent = agent
        self.__plumbing = True
        atom.Atom.__init__(self,names='output',creator=self.__create,wrecker=self.__wreck,protocols='create')

    def __wreck(self,i,o):
        if self.__plumbing:
            e.unplumb()

    def listinstances(self):
        return [ self[i].get_property_long('ordinal',0) for i in self ]

    def rpc_listinstances(self,arg):
        i = self.listinstances()
        return logic.render_termlist(i)

    def rpc_instancename(self,a):
        return 'keygroup output'

    def rpc_createinstance(self,arg):
        name = int(arg)
        outputs = self.listinstances()

        if name in outputs:
            return async.failure('output in use')

        output = self.create(name)
        return output.id()

    def rpc_delinstance(self,arg):
        for k,v in self.items():
            if arg == v.id():
                v.notify_destroy()
                del self[k]
                self.__outputs_changed()
                return arg

        return async.failure('output not in use')

    @async.coroutine('internal error')
    def load_state(self,state,delegate,phase):
        self.__plumbing = False

        for v in self.values():
            v.enable(False)
            v.unplumb()

        yield atom.Atom.load_state(self,state,delegate,phase)

        for v in self.values():
            v.plumb()

        for v in self.values():
            enabled = v[23].get_value()
            v.enable(enabled)

        self.__plumbing = True
        self.__outputs_changed()
        self.update_status_indexes()

    def __create(self,i):
        return Output(self,i)

    def create(self,ordinal=None):
        slot = self.find_hole()
        output = Output(self,slot)
        output.set_ordinal(ordinal)
        output.plumb()
        self[slot] = output

        self.__outputs_changed()

        return output

    def output_selector(self,v):
        if v.is_tuple():
            hardness = v.as_tuple_value(2).as_long()
            if hardness > 0:
                column = int(v.as_tuple_value(0).as_tuple_value(0).as_float())
                row = int(v.as_tuple_value(0).as_tuple_value(1).as_float())
                for k,o in self.items():
                    if o.key_coordinate().equals(column, row, self.agent.controller.gettuple('columnlen')):
                        self.agent.mode_selector.gate_input(k)(piw.makebool_nb(True,v.time()))
                        break

    def uncreate(self,oid):
        for k,v in self.items():
            if v.id()==oid:
                v.notify_destroy()
                del self[k]
                self.__outputs_changed()
                return True

        return False

    def activate(self,name):
        for k,v in self.items():
            print 'activate',name,k
            if k==name:
                self.agent.mode_selector.activate(k)
                break

    def __outputs_changed(self):
        # check if there's just a single output
        outputs = self.values()
        if len(outputs)==1:
            outputs[0].enable(True)

        # update the size of the status output light buffer
        k = self.keys();
        if not len(k):
            self.agent.status_lights.set_size(0)
        else:
            self.agent.status_lights.set_size(max(k))

    def update_status_indexes(self):
        for v in self.values():
            v.update_status_index()


class Agent(agent.Agent):
    def __init__(self, address, ordinal):
        agent.Agent.__init__(self, signature=version, names='keygroup', container=8, ordinal=ordinal)

        self.__active_blinker = None
        self.__cur_size = 0

        self.__private = node.Server()
        self.set_private(self.__private)

        self.domain = piw.clockdomain_ctl()
        self.domain.set_source(piw.makestring('*',0))

        self.mapper = piw.keygroup_mapper()

        self[15] = bundles.Output(1,False,names='light output',protocols='revconnect')
        self.lights = bundles.Splitter(self.domain,self[15])
        self.status_mapper = piw.function1(False,1,1,piw.makenull(0),self.lights.cookie())
        self.status_mapper.set_functor(self.mapper.light_filter())
        self.light_switch = piw.multiplexer(self.status_mapper.cookie(),self.domain)

        self.kclone = piw.clone(False) # keys
        self.s1clone = piw.clone(False) # strip 1
        self.s2clone = piw.clone(False) # strip 2
        self.bclone = piw.clone(False) # breath
        self.cclone = piw.clone(True) # controller
        self.pedal1_clone = piw.clone(False) # pedal 1
        self.pedal2_clone = piw.clone(False) # pedal 2
        self.pedal3_clone = piw.clone(False) # pedal 3
        self.pedal4_clone = piw.clone(False) # pedal 4

        self.kclone.set_policy(False)

        self.keymapfilter = piw.clone(True) # keys
        self.keymapfilter.set_filtered_data_output(1, self.kclone.cookie(), self.mapper.key_filter(), 5)

        self.s1input = bundles.ScalarInput(self.s1clone.cookie(),self.domain,signals=(1,2))
        self.s2input = bundles.ScalarInput(self.s2clone.cookie(),self.domain,signals=(1,2))
        self.binput = bundles.ScalarInput(self.bclone.cookie(),self.domain,signals=(1,))
        self[4] = atom.Atom(domain=domain.BoundedFloat(-1,1),policy=self.s1input.nodefault_policy(1,False),names='strip position input',ordinal=1)
        self[6] = atom.Atom(domain=domain.BoundedFloat(-1,1),policy=self.s2input.nodefault_policy(1,False),names='strip position input',ordinal=2)
        self[5] = atom.Atom(domain=domain.BoundedFloat(0,1),policy=self.binput.nodefault_policy(1,False),names='breath input')
        self[2] = atom.Atom(domain=domain.BoundedFloat(-1,1),policy=self.s1input.nodefault_policy(2,False),names='absolute strip input',ordinal=1)
        self[7] = atom.Atom(domain=domain.BoundedFloat(-1,1),policy=self.s2input.nodefault_policy(2,False),names='absolute strip input',ordinal=2)

        self.input_pedal1 = bundles.VectorInput(self.pedal1_clone.cookie(), self.domain, signals=(1,))
        self.input_pedal2 = bundles.VectorInput(self.pedal2_clone.cookie(), self.domain, signals=(1,))
        self.input_pedal3 = bundles.VectorInput(self.pedal3_clone.cookie(), self.domain, signals=(1,))
        self.input_pedal4 = bundles.VectorInput(self.pedal4_clone.cookie(), self.domain, signals=(1,))
        self[30] = atom.Atom(domain=domain.Aniso(), policy=self.input_pedal1.vector_policy(1,False),names='pedal input', ordinal=1)
        self[31] = atom.Atom(domain=domain.Aniso(), policy=self.input_pedal2.vector_policy(1,False),names='pedal input', ordinal=2)
        self[32] = atom.Atom(domain=domain.Aniso(), policy=self.input_pedal3.vector_policy(1,False),names='pedal input', ordinal=3)
        self[33] = atom.Atom(domain=domain.Aniso(), policy=self.input_pedal4.vector_policy(1,False),names='pedal input', ordinal=4)

        self.kinput = bundles.VectorInput(self.keymapfilter.cookie(),self.domain,signals=(2,3,4,5),threshold=10)

        self[12] = atom.Atom(domain=domain.BoundedFloat(0,1), policy=self.kinput.vector_policy(2,False), names='pressure input')
        self[13] = atom.Atom(domain=domain.BoundedFloat(-1,1), policy=self.kinput.vector_policy(3,False), names='roll input')
        self[14] = atom.Atom(domain=domain.BoundedFloat(-1,1), policy=self.kinput.vector_policy(4,False), names='yaw input')
        self[22] = atom.Atom(domain=domain.Aniso(), policy=self.kinput.vector_policy(5,False), names='key input')

        self.controller = Controller(self,self.cclone.cookie())
        self.__private[2] = self.controller.state()

        self.keychoice = utils.make_change_nb(piw.slowchange(utils.changify(self.__choice)))
        self.keychoicefunctor = piw.functor_backend(5,True)
        self.keychoicefunctor.set_gfunctor(self.keychoice)
        self.keymapfilter.set_output(250,self.keychoicefunctor.cookie())
        self.keymapfilter.enable(250,False)

        self.status_buffer = piw.statusbuffer(self.light_switch.gate_input(),251,self.light_switch.get_input(251))
        self.status_buffer.autosend(False)
        lightselection = self.status_buffer.enabler()
        modeselection = utils.make_change_nb(piw.slowchange(utils.changify(self.__mode_selection)))
        self.mode_selector = piw.selector(self.light_switch.get_input(250),lightselection,modeselection,250,False)

        self[36] = bundles.Output(1,False,names='status output')
        self.status_output = bundles.Splitter(self.domain, self[36])
        self.status_lights = piw.lightsource(piw.change_nb(), 0, self.status_output.cookie())

        self.modepulse = piw.changelist_nb()
        piw.changelist_connect_nb(self.modepulse,self.status_buffer.blinker())
        piw.changelist_connect_nb(self.modepulse,self.mode_selector.mode_input())

        self.modekey_handler = piw.modekey_handler()
        self[23] = atom.Atom(domain=domain.Aniso(), names='mode key input', policy=policy.FastPolicy(self.modepulse,policy.FilterStreamPolicy(self.modekey_handler.key_filter())))
        self[24] = atom.Atom(domain=domain.BoundedInt(-32767,32767), names='mode key column', init=None, policy=atom.default_policy(self.__change_mode_key_column))
        self[25] = atom.Atom(domain=domain.BoundedInt(-32767,32767), names='mode key row', init=None, policy=atom.default_policy(self.__change_mode_key_row))
        self[26] = atom.Atom(domain=domain.Bool(),names='mode key column end relative',init=False,policy=atom.default_policy(self.__change_mode_key_column_endrel))
        self[28] = atom.Atom(domain=domain.Bool(),names='mode key row end relative',init=False,policy=atom.default_policy(self.__change_mode_key_row_endrel))
        self[27] = atom.Atom(domain=domain.String(), init='[]', names='physical mapping', protocols='mapper', policy=atom.default_policy(self.__set_physical_key_map))
        self[34] = atom.Atom(domain=domain.String(), init='[]', names='musical mapping', protocols='mapper', policy=atom.default_policy(self.__set_musical_key_map))
        self[35] = atom.Atom(domain=domain.String(), init='[]', names='course offset', policy=atom.default_policy(self.__set_course_offset))
        self[38] = atom.Atom(domain=domain.String(), init='Keygroup', names='label category', policy=atom.default_policy(self.__set_category))
        self[39] = atom.Atom(domain=domain.String(), init='', names='label', policy=atom.default_policy(self.__set_label))

        self.add_verb2(3,'set([un],None)',callback=self.__untune)

        self.add_verb2(5,'create([],None,role(None,[mass([output])]))',self.__create)
        self.add_verb2(6,'create([un],None,role(None,[concrete,singular,partof(~(a)#1)]))', self.__uncreate)
        self.add_verb2(7,'choose([],None,role(None,[matches([key])]),option(as,[numeric]))',self.__choose)
        self.add_verb2(11,'choose([un],None)',self.__unchoose)
        
        self.add_verb2(8,'set([],None,role(None,[tagged_ideal([~server,course],[offset])]),role(to,[mass([semitone])]))', callback=self.__set_course_semi)
        self.add_verb2(9,'set([],None,role(None,[tagged_ideal([~server,course],[offset])]),role(to,[mass([interval])]))', callback=self.__set_course_int)

        self.add_verb2(12,'clear([],None,role(None,[matches([musical])]))', callback=self.__musicalclear)
        self.add_verb2(16,'clear([],None,role(None,[mass([course])]))', callback=self.__courseclear)
        self.add_verb2(17,'clear([],None,role(None,[matches([physical])]))', callback=self.__physicalclear)
        self.add_verb2(18,'clear([],None,role(None,[mass([column])]))', callback=self.__columnclear)

        self.add_verb2(13,'add([],None,role(None,[coord(physical,[column],[row])]),role(to,[coord(physical,[column],[row])]))', callback=self.__kadd_physical)
        self.add_verb2(14,'add([],None,role(None,[coord(musical,[course],[key])]),role(to,[coord(musical,[course],[key])]))', callback=self.__kadd_musical)

        self.add_verb2(15,'choose([],None,role(None,[mass([output])]))', callback=self.__ochoose, status_action=self.__ostatus)

        th=(T('stageinc',1),T('inc',1),T('biginc',1),T('control','updown'))

        self[9] = atom.Atom(domain=domain.BoundedFloatOrNull(-20,20,hints=th),init=None,policy=atom.default_policy(self.__change_base),names='base note')

        self[16] = VirtualCourse(self.controller)

        self.__upstream_columnlen = None
        self.__upstream_courselen = None
        self.upstream_labels = None

        self.cfunctor = piw.functor_backend(1,True)
        self.cinput = bundles.ScalarInput(self.cfunctor.cookie(),self.domain,signals=(1,))
        self[17] = atom.Atom(domain=domain.Aniso(), policy=self.cinput.nodefault_policy(1,False),names='controller input')
        self.cfunctor.set_functor(piw.pathnull(0),utils.make_change_nb(piw.slowchange(utils.changify(self.__upstream))))

        self.__upstream_modekey_columnlen = None

        self.cmkfunctor = piw.functor_backend(1,True)
        self.cmkinput = bundles.ScalarInput(self.cmkfunctor.cookie(),self.domain,signals=(1,))
        self[37] = atom.Atom(domain=domain.Aniso(), policy=self.cmkinput.nodefault_policy(1,False),names='mode key controller input')
        self.cmkfunctor.set_functor(piw.pathnull(0),utils.make_change_nb(piw.slowchange(utils.changify(self.__upstream_modekey))))

        self[18] = atom.Atom(domain=domain.BoundedFloatOrNull(-1,9,hints=th),init=None,policy=atom.default_policy(self.__change_octave),names='octave')

        self[19] = atom.Atom(domain=domain.BoundedFloatOrNull(0,12,hints=th),init=None,policy=atom.default_policy(self.__change_tonic),names='tonic',protocols='bind set',container=(None,'tonic',self.verb_container()))
        self[19].add_verb2(1,'set([],~a,role(None,[instance(~self)]),role(to,[ideal([None,note]),singular]))',create_action=self.__tune_tonic_fast,callback=self.__tune_tonic)

        self[20] = atom.Atom(domain=domain.String(),init='',policy=atom.default_policy(self.__change_scale),names='scale',protocols='bind set',container=(None,'scale',self.verb_container()))
        self[20].add_verb2(1,'set([],~a,role(None,[instance(~self)]),role(to,[ideal([None,scale]),singular]))',create_action=self.__tune_scale_fast,callback=self.__tune_scale)
        
        self[21] = atom.Atom(domain=domain.BoundedFloatOrNull(0,20,hints=(T('stageinc',0.1),T('inc',0.1),T('biginc',1),T('control','updown'))),init=0.5,policy=atom.default_policy(self.__change_blinktime),names='blink')

        self[1] = OutputList(self)

        self.outputchoice = utils.make_change_nb(piw.slowchange(utils.changify(self[1].output_selector)))
        self.outputchoicefunctor = piw.functor_backend(5,True)
        self.outputchoicefunctor.set_gfunctor(self.outputchoice)
        self.kclone.set_output(250,self.outputchoicefunctor.cookie())
        self.kclone.enable(250,False)

        self.controller.update_labels()

    def agent_postload(self,filename):
        self.status_buffer.send()

    def load_state(self,state,delegate,phase):
        result = agent.Agent.load_state(self,state,delegate,phase)
        self.controller.update_labels()
        return result

    def property_change(self,key,value,delegate):
        if key == 'name' or key == 'cname':
            self.controller.update_labels()

    def rpc_fetch_sourcekeys(self,arg):
        name = str(arg)
        result = []

        if name == self[27].get_property_string('cname') and self.__upstream_columnlen:
            row = 0
            for cl in self.__upstream_columnlen:
                row += 1
                for column in range(1,cl+1):
                    result.append((column,row))
        elif name == self[34].get_property_string('cname') and self.__upstream_courselen:
            course = 0
            for cl in self.__upstream_courselen:
                course += 1
                for key in range(1,cl+1):
                    result.append((course,key))

        return logic.render_term(result)

    def rpc_choose(self,arg):
        course = int(arg)
        self.__choose_base(course)

    def rpc_unchoose(self,arg):
        self.__unchoose_base()

    def __mode_selection(self,d):
        if d.as_long():
            self.kclone.enable(250,True)
        else:
            self.kclone.enable(250,False)

    def __change_scale(self,val):
        self[20].set_value(val)
        self.controller.thing_changed(self[20].get_data(),'scale')
        return False

    def __change_octave(self,val):
        self[18].set_value(val)
        self.controller.thing_changed(self[18].get_data(),'octave')
        return False

    def __change_tonic(self,val):
        self[19].set_value(val)
        self.controller.thing_changed(self[19].get_data(),'tonic')
        return False

    def __change_base(self,val):
        self[9].set_value(val)
        self.controller.thing_changed(self[9].get_data(),'base')
        return False

    def __change_blinktime(self,val):
        if not val:
            val = 0
        self[21].set_value(val)
        self.status_buffer.set_blink_time(float(val))
        return False

    def __change_mode_key_column(self,val):
        self[24].set_value(val)
        self.__update_mode_key()
        return False

    def __change_mode_key_row(self,val):
        self[25].set_value(val)
        self.__update_mode_key()
        return False

    def __change_mode_key_column_endrel(self,val):
        self[26].set_value(val)
        self.__update_mode_key()
        return False

    def __change_mode_key_row_endrel(self,val):
        self[28].set_value(val)
        self.__update_mode_key()
        return False

    def __update_mode_key(self):
        self.modekey_handler.set_modekey(piw.coordinate(self[24].get_value(), self[25].get_value(), self[26].get_value(), self[28].get_value()))

    def __upstream(self,c):
        try:
            if not c.is_dict(): return 0

            refresh_mappings = False

            # store the upstream column lengths
            cl = c.as_dict_lookup('columnlen')
            new_cl = None
            if cl.is_tuple():
                new_cl = [ i.as_long() for i in utils.tuple_items(cl) ]
            if new_cl and not self.__upstream_modekey_columnlen:
                self.modekey_handler.set_upstream_columnlength(cl)

            if new_cl != self.__upstream_columnlen:
                refresh_mappings = True

            self.__upstream_columnlen = new_cl

            # store the upstream course lengths
            cl = c.as_dict_lookup('courselen')
            new_cl = None
            if cl.is_tuple():
                new_cl = [ i.as_long() for i in utils.tuple_items(cl) ]

            if new_cl != self.__upstream_courselen:
                refresh_mappings = True

            self.__upstream_courselen = new_cl

            # refresh the mappings
            if refresh_mappings:
                self.__set_physical_mapping(self.__current_physical_mapping())
                self.__set_musical_mapping(self.__current_musical_mapping())

            # store the upstream labels
            labels = c.as_dict_lookup('labels')
            new_labels = None
            if labels.is_tuple():
                new_labels = utils.tuple_items(labels)

            if new_labels != self.upstream_labels:
                self.upstream_labels = new_labels
                self.controller.update_labels()

        except:
            return 0

    def __upstream_modekey(self,c):
        try:
            if not c.is_dict(): return 0

            # store the upstream column lengths
            cl = c.as_dict_lookup('columnlen')
            new_cl = None
            if cl.is_tuple():
                self.modekey_handler.set_upstream_columnlength(cl)
                new_cl = [ i.as_long() for i in utils.tuple_items(cl) ]

            self.__upstream_modekey_columnlen = new_cl

        except:
            return 0

    def __set_course_semi(self,subject,course,interval):
        (typ,id) = action.crack_ideal(action.arg_objects(course)[0])
        course = int(id)
        semis = action.mass_quantity(interval)
        self.controller.set_course_semis(int(course),semis)
        self[35].set_value(logic.render_term(self.controller.get_course_offsets()))
        return action.nosync_return()

    def __set_course_int(self,subject,course,interval):
        (typ,id) = action.crack_ideal(action.arg_objects(course)[0])
        course = int(id)
        ints = action.mass_quantity(interval)
        self.controller.set_course_steps(int(course),ints)
        self[35].set_value(logic.render_term(self.controller.get_course_offsets()))
        return action.nosync_return()

    def __set_course_offset(self,value):
        self.controller.set_course_offsets(logic.parse_clause(value))
        self[35].set_value(value)
 
    def __set_category(self,v):
        if v != self[38].get_value():
            self[38].set_value(v)
            self.controller.update_labels()
 
    def __set_label(self,v):
        if v != self[39].get_value():
            self[39].set_value(v)
            self.controller.update_labels()

    def __tune_tonic_fast(self,ctx,subj,dummy,arg):
        type,thing = action.crack_ideal(action.arg_objects(arg)[0])
        value = int(thing)
        chg = piw.change2(self.controller.changetonic(value),piw.slowchange(utils.changify(SlowTonicChange(self,value).change)))
        return chg,None

    def __tune_scale_fast(self,ctx,subj,dummy,arg):
        type,thing = action.crack_ideal(action.arg_objects(arg)[0])
        value = action.marshal(thing)
        chg = piw.change2(self.controller.changescale(value),piw.slowchange(utils.changify(SlowScaleChange(self,value).change)))
        return chg,None

    def __tune_tonic(self,subj,dummy,arg):
        type,thing = action.crack_ideal(action.arg_objects(arg)[0])
        self[19].set_value(int(thing))
        self.controller.thing_changed(self[19].get_data(),'tonic')
        return action.nosync_return()

    def __tune_scale(self,subj,dummy,arg):
        type,thing = action.crack_ideal(action.arg_objects(arg)[0])
        self[20].set_value(action.marshal(thing))
        self.controller.thing_changed(self[20].get_data(),'scale')
        return action.nosync_return()

    def __untune(self,subj):
        self[18].set_value(None)
        self.controller.thing_changed(self[18].get_data(),'octave')

        self[19].set_value(None)
        self.controller.thing_changed(self[19].get_data(),'tonic')
       
        self[20].set_value('')
        self.controller.thing_changed(self[20].get_data(),'scale') 
        return action.nosync_return()

    def keygroup_size(self):
        return self.__cur_size

    def key_choice(self):
        return self.__choices

    def __ochoose(self,subj,name):
        name = int(action.abstract_wordlist(name)[0])
        self[1].activate(name)

    def __ostatus(self,subj,name):
        name = int(action.abstract_wordlist(name)[0])
        return 'dsc(~(a)"#36","%s")' % name

    def __create(self,subj,name):
        name = int(action.abstract_wordlist(name)[0])
        o = self[1].create(name)
        return action.concrete_return(o.id())

    def __uncreate(self,subj,grp):
        a = action.concrete_object(grp)
        if self[1].uncreate(a):
            return async.success(action.removed_return(a))
        return async.success(errors.doesnt_exist('output','un create'))

    def __musicalclear(self,subject,name):
        self.__set_musical_mapping(())
        return

    def __courseclear(self,subject,course):
        if course is None: return

        course = int(action.mass_quantity(course))
        musical_mapping = []

        for m in self.__current_musical_mapping():
            if m[1][0] != course:
                musical_mapping.append(m)

        self.__set_musical_mapping(musical_mapping)

    def __physicalclear(self,subject,name):
        self.__set_physical_mapping(())

    def __columnclear(self,subject,column):
        if column is None: return

        column = int(action.mass_quantity(column))
        physical_mapping = []

        for p in self.__current_physical_mapping():
            if p[1][0] != column:
                physical_mapping.append(p)

        self.__set_physical_mapping(physical_mapping)

    def __kadd_physical(self,subject,kfrom,kto):
        fcolumn,frow = action.coord_value(kfrom)
        tcolumn,trow = action.coord_value(kto)

        old = self.__current_physical_mapping()
        new = []

        for ((fx,fy),(tx,ty)) in old:
            if fx==fcolumn and fy==frow:
                continue
            if tx==tcolumn and ty==trow:
                continue
            new.append(((fx,fy),(tx,ty)))
            
        new.append(((fcolumn,frow),(tcolumn,trow)))
        self.__set_physical_mapping(new)

    def __kadd_musical(self,subject,kfrom,kto):
        fcourse,fkey = action.coord_value(kfrom)
        tcourse,tkey = action.coord_value(kto)

        old = self.__current_musical_mapping()
        new = []

        for ((fx,fy),(tx,ty)) in old:
            if fx==fcourse and fy==fkey:
                continue
            if tx==tcourse and ty==tkey:
                continue
            new.append(((fx,fy),(tx,ty)))
            
        new.append(((fcourse,fkey),(tcourse,tkey)))
        self.__set_musical_mapping(new)

    def __choose(self,subject,dummy,course):
        c = int(action.abstract_string(course)) if course else None
        self.__choose_base(c)

    def __choose_base(self,course):
        # initialize the choices and the active course
        self.__choices = []
        self.__coursekeys = []
        self.__mappedkeys = []
        self.__course = course

        # disable the keymap filter and install a pass-through light functor
        self.status_mapper.set_functor(piw.null_filter())
        self.keymapfilter.enable(1,False)
        self.keymapfilter.enable(250,False)
        self.keymapfilter.enable(250,True)

        # store the upstream musical keys that correspond to the currently selected
        # musical keys for the course that is being chosen, if no specific course was
        # chosen, all already selected upstream musical keys are added
        # additionally, all mapped upstream keys are stored also
        # this is used to highlight these keys differently after the fix selection is made
        for entry in self.__current_musical_mapping():
            mus_in = entry[0]
            mus_out = entry[1]
            if not self.__course or mus_out[0] == self.__course:
                self.__coursekeys.append(mus_in)
            self.__mappedkeys.append(mus_in)

        # go over the upstream courses and their lengths to highlight the musical
        # keys as the choose mode starts
        if self.__upstream_courselen:
            course = 0
            for courselen in self.__upstream_courselen:
                course += 1
                for i in range(1,courselen+1):
                    key = (course,i)
                    if key in self.__mappedkeys:
                        if key in self.__coursekeys:
                            self.status_buffer.set_status(True,piw.coordinate(course,i),const.status_choose_active)
                        else:
                            self.status_buffer.set_status(True,piw.coordinate(course,i),const.status_choose_used)
                    else:
                        self.status_buffer.set_status(True,piw.coordinate(course,i),const.status_choose_available)

        self.status_buffer.send()

        # switch the status buffer to display the choose keys and hook up
        # the key selection to the changelist of the key input
        self.status_buffer.override(True)
        self.mode_selector.choose(True)

    def __stop_choosing(self):
        self.keymapfilter.enable(250,False)
        self.status_buffer.override(False)
        self.mode_selector.choose(False)
        self.status_mapper.set_functor(self.mapper.light_filter())

    def __choice(self,v):
        choice = utils.key_to_lists(v)
        if not choice: return
        if not choice[2]: return
        # remove the hardness so that it's not part of the identity of the choice
        del choice[2]

        # if this choice is the same as the previous one
        # stop choose mode and store the new mapping
        if self.__choices and choice==self.__choices[-1]:
            self.__stop_choosing()
            self.__do_mapping()
            return

        # if this is a new choice, store it and adapt the status leds
        if not choice in self.__choices:
            self.__choices.append(choice)
            key = choice[1]
            for ck in self.__coursekeys:
                self.status_buffer.set_status(True,piw.coordinate(ck[0],ck[1]),const.status_choose_used)
            self.__coursekeys=[]
            self.status_buffer.set_status(True,piw.coordinate(key[0],key[1]),const.status_choose_active)
            self.status_buffer.send()

    def __unchoose(self,subject):
        self.__unchoose_base()

    def __unchoose_base(self):
        self.__stop_choosing()
        self.keymapfilter.enable(1,True)

    def __do_mapping(self):
        musical_mapping = []
        physical_mapping = []
        physical_ins = set() 

        # if the mapping selection was for a particular course,
        if self.__course:
            # preserve all the other courses
            for m in self.__current_musical_mapping():
                if m[1][0] != self.__course:
                    musical_mapping.append(m)

            # also preserve the existing physical input coordinates
            for m in self.__current_physical_mapping():
                physical_ins.add(m[0])

        # create a new musical course mapping based on the order
        # in which the choices were made,
        # also store the additional physical input coordinates
        course = self.__course
        if not course: course = 1
        key = 1
        for c in self.__choices:
            musical_mapping.append( ((int(c[1][0]),int(c[1][1])),(course,key)) )
            key += 1
            physical_ins.add( (int(c[0][0]),int(c[0][1])) )
        
        # build a new physical mapping based on the boundaries
        # of the input coordinates
        last_in_column = 0
        physical_out_column = 0
        physical_out_row = 0 
        for p in sorted(physical_ins):
            if p[0] != last_in_column:
                physical_out_column += 1
                physical_out_row = 0
                last_in_column = p[0]
            physical_out_row += 1
            physical_mapping.append( (p,(physical_out_column,physical_out_row)) )
        
        # activate the new musical mapping
        self.__set_musical_mapping(musical_mapping)
        
        # activate the new physical mapping
        self.__set_physical_mapping(physical_mapping)

    def __current_physical_mapping(self):
        return logic.parse_clause(self[27].get_value())

    def __current_musical_mapping(self):
        return logic.parse_clause(self[34].get_value())

    def __sanitize_mapping(self,mapping,desc=""):
        if mapping is None:
            mapping = list()

        mapping = list(mapping)
        mapping.sort()

        # reverse the mapping so that the target coordinates come first
        # allowing them to be sorted easy afterwards
        # also prune the mapping so that only one of each source coordinate
        # remains
        prev_entry = None
        reverse_mapping = list()
        for entry in mapping:
            if entry[0][0] <= 0 or entry[0][1] <= 0 or entry[1][0] <= 0 or entry[1][1] <= 0:
                #print 'forward',desc,'ignoring',entry
                continue
            if entry[0] == prev_entry:
                #print 'forward',desc,'ignoring',entry
                continue
            prev_entry = entry[0]
            reverse_mapping.append( (entry[1],entry[0]) )
        reverse_mapping.sort()

        # prune the reverse mapping to only preserve valid entries
        prev_entry = None
        pruned_mapping = list()
        pruned_reverse = list()
        for entry in reverse_mapping:
            if entry[0] == prev_entry:
                #print 'reverse',desc,'ignoring',entry
                continue
            prev_entry = entry[0]
            pruned_mapping.append( (entry[1],entry[0]) )
            pruned_reverse.append(entry)

        pruned_mapping.sort()

        #print 'forward',desc,pruned_mapping
        #print 'reverse',desc,pruned_reverse

        return (pruned_mapping,pruned_reverse)


    def __set_physical_key_map(self,value):
        mapping = logic.parse_clause(value)
        self.__set_physical_mapping(mapping)

    def __set_physical_mapping(self,mapping):
        mapper = self.mapper
        mapper.clear_physical_mapping()

        mapping,reverse_mapping = self.__sanitize_mapping(mapping,'physical')

        # initialize the column offsets
        columnoffsets = []
        if self.__upstream_columnlen:
            for i in self.__upstream_columnlen:
                columnoffsets.append(None)

        # iterate over the mapping that's sorted by out key and determine
        # the column lengths and column offsets
        columnlengths = dict()
        max_column = 0
        for entry in reverse_mapping:
            column_in = entry[1][0]
            row_in = entry[1][1]
            column_out = entry[0][0]
            max_column = max(max_column,column_out)
            if column_out <= len(columnoffsets) and columnoffsets[column_out-1] is None:
                columnoffsets[column_out-1] = row_in-1
            if column_out in columnlengths:
                columnlengths[column_out] += 1
            else:
                columnlengths[column_out] = 1

        # re-iterate over the mapping while adding each entry to the underlying mapper
        for entry in reverse_mapping:

            # calculate the entry's input key data
            column_in = entry[1][0]
            row_in = entry[1][1]
            column_in_rel = 0
            row_in_rel = 0
            if self.__upstream_columnlen and column_in <= len(self.__upstream_columnlen):
                column_in_rel = len(self.__upstream_columnlen) + 1 - column_in
                row_in_rel = self.__upstream_columnlen[column_in-1] + 1 - row_in

            # calculate the entry's output key data
            column_out = entry[0][0]
            row_out = entry[0][1]
            column_out_rel =  max_column + 1 - column_out
            row_out_rel = columnlengths[column_out] + 1 - row_out

            # add the mapping for this entry
            mapper.set_physical_mapping(column_in,row_in,column_in_rel,row_in_rel,column_out,row_out,column_out_rel,row_out_rel)

        # activate the physical mappings
        mapper.activate_physical_mapping()

        # adapt the controller stream
        if len(mapping):
            self.controller.setlist('columnlen', [piw.makelong(r,0) for r in columnlengths.values()])
            self.controller.setlist('columnoffset', [piw.makelong(r,0) if r is not None else piw.makenull(0) for r in columnoffsets])
        else:
            # if the mapping was empty, use the upstream column lengths and no offsets
            self.controller.setlist('columnlen', [piw.makelong(r,0) for r in self.__upstream_columnlen or []])
            self.controller.setlist('columnoffset', [piw.makelong(0,0) for r in self.__upstream_columnlen or []])

        # update the outputs status indexes
        self[1].update_status_indexes()

        # store the mapping description in the state of the agent
        self[27].set_value(logic.render_term(mapping))

        self.keymapfilter.enable(1,False)
        self.keymapfilter.enable(1,True)

        self.status_buffer.set_blink_geometry(self.controller.gettuple('columnlen'))

    def __set_musical_key_map(self,value):
        mapping = logic.parse_clause(value)
        self.__set_musical_mapping(mapping)

    def __set_musical_mapping(self,mapping):
        mapper = self.mapper
        mapper.clear_musical_mapping()

        mapping,reverse_mapping = self.__sanitize_mapping(mapping,'musical')

        # iterate over the mapping that's sorted by out key and calculate
        # each course length
        courselengths = dict()
        max_course = 0
        for entry in reverse_mapping:
            course_out = entry[0][0]
            max_course = max(max_course,course_out)
            if course_out in courselengths:
                courselengths[course_out] += 1
            else:
                courselengths[course_out] = 1

        # iterate over the mapping that's sorted by out key and calculate
        # the length of each course
        for entry in reverse_mapping:

            # calculate the entry's input key data
            course_in = entry[1][0]
            key_in = entry[1][1]
            course_in_rel = 0
            key_in_rel = 0
            if self.__upstream_courselen and course_in <= len(self.__upstream_courselen):
                course_in_rel = len(self.__upstream_courselen) + 1 - course_in
                key_in_rel = self.__upstream_courselen[course_in-1] + 1 - key_in

            # calculate the entry's output key data
            course_out = entry[0][0]
            key_out = entry[0][1]
            course_out_rel = max_course + 1 - course_out
            key_out_rel = courselengths[course_out] + 1 - key_out

            # add the mapping for this entry
            mapper.set_musical_mapping(course_in,key_in,course_in_rel,key_in_rel,course_out,key_out,course_out_rel,key_out_rel)

        # activate the musical mappings
        mapper.activate_musical_mapping()

        # adapt the controller stream
        if len(mapping):
            self.controller.setlist('courselen', [piw.makelong(c,0) for c in courselengths.values()])
            courseoffsets = logic.parse_clause(self[35].get_value())
            if not courseoffsets:
                courseoffsets = list()
            # ensure that there's a course offset for each course
            if len(courseoffsets) < max_course:
                courseoffsets = list(courseoffsets)
                courseoffsets.extend( [ 0.0 for i in range(max_course-len(courseoffsets)) ] )
            self[35].set_value(logic.render_term(courseoffsets))
            self.controller.setlist('courseoffset', [piw.makefloat(o,0) for o in courseoffsets])
        else:
            # if the mapping was empty, use the upstream courselen
            self.controller.setlist('courselen', [piw.makelong(c,0) for c in self.__upstream_courselen or []])
            self.controller.setlist('courseoffset', [piw.makefloat(0.0,0) for c in self.__upstream_courselen or []])

        # store the mapping description in the state of the agent
        self[34].set_value(logic.render_term(mapping))

        self.keymapfilter.enable(1,False)
        self.keymapfilter.enable(1,True)


agent.main(Agent)
