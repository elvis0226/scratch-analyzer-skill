"""Extract a Scratch 3 script as scratchblocks v3 text. No external Python packages."""
import json,zipfile,argparse,sys

def convert(path, sprite='按鈕(兼導演)', broadcast='計算', block_id=None, event='broadcast'):
    with zipfile.ZipFile(path) as z: project=json.loads(z.read('project.json'))
    target=next((t for t in project['targets'] if t['name']==sprite), None)
    if target is None: raise ValueError(f'Sprite not found: {sprite}')
    blocks=target['blocks']
    active=set()
    def field(b,k,default=''):
        return str(b.get('fields',{}).get(k,[default])[0])
    def expr(i):
        if not i:return ''
        if isinstance(i,str):return expression_by_id(i)
        if isinstance(i,list):
            v=i[1] if len(i)>1 else None
            if isinstance(v,str):return expression_by_id(v)
            if isinstance(v,list) and len(v)>1:
                return f'({v[1]})' if v[0]==12 else str(v[1])
        return ''
    def inp(b,k):return expr(b.get('inputs',{}).get(k))
    def value(b,k):
        v=inp(b,k)
        return v if v.startswith(('(', '<')) else f'({v})'
    def expression_by_id(block_id):
        if block_id in active: raise ValueError(f'Cycle in expression at block {block_id}')
        if block_id not in blocks: raise ValueError(f'Missing block {block_id}')
        active.add(block_id)
        try: return block_expr(blocks[block_id],block_id)
        finally: active.remove(block_id)
    def block_expr(b,block_id):
        o=b['opcode']
        if o=='operator_equals':return f'<{value(b,"OPERAND1")} = {value(b,"OPERAND2")}>'
        if o=='operator_and':return f'<{inp(b,"OPERAND1")} and {inp(b,"OPERAND2")}>'
        if o=='operator_or':return f'<{inp(b,"OPERAND1")} or {inp(b,"OPERAND2")}>'
        if o=='operator_not':return f'<not {inp(b,"OPERAND")}>'
        if o=='operator_multiply':return f'({value(b,"NUM1")} * {value(b,"NUM2")})'
        if o=='operator_random':return f'(pick random {value(b,"FROM")} to {value(b,"TO")})'
        if o=='operator_add':return f'({inp(b,"NUM1")} + {inp(b,"NUM2")})'
        if o=='operator_subtract':return f'({inp(b,"NUM1")} - {inp(b,"NUM2")})'
        if o=='operator_gt':return f'<{inp(b,"OPERAND1")} > {inp(b,"OPERAND2")}>'
        if o=='operator_lt':return f'<{inp(b,"OPERAND1")} < {inp(b,"OPERAND2")}>'
        if o=='sensing_of':return f'([{field(b,"PROPERTY")} v] of [{inp(b,"OBJECT")} v])'
        if o=='sensing_of_object_menu':return field(b,'OBJECT')
        if o=='event_broadcast_menu':return field(b,'BROADCAST_OPTION')
        if o=='sensing_answer':return '(answer)'
        if o=='sensing_mousedown':return '<mouse down?>'
        if o=='sensing_touchingobject':return f'<touching [{inp(b,"TOUCHINGOBJECTMENU")} v]?>'
        if o=='sensing_touchingobjectmenu':return {'_edge_':'edge','_mouse_':'mouse-pointer'}.get(field(b,'TOUCHINGOBJECTMENU'),field(b,'TOUCHINGOBJECTMENU'))
        if o=='motion_pointtowards_menu':return {'_mouse_':'mouse-pointer'}.get(field(b,'TOWARDS'),field(b,'TOWARDS'))
        if o=='control_create_clone_of_menu':return {'_myself_':'myself'}.get(field(b,'CLONE_OPTION'),field(b,'CLONE_OPTION'))
        if o=='looks_costume':return field(b,'COSTUME')
        if o=='data_variable':return f'({field(b,"VARIABLE")})'
        if o=='operator_join':return f'(join {inp(b,"STRING1")} {inp(b,"STRING2")})'
        if o=='operator_length':return f'(length of {value(b,"STRING")})'
        if o=='operator_letter_of':return f'(letter {value(b,"LETTER")} of {value(b,"STRING")})'
        if o=='data_lengthoflist':return f'(length of [{field(b,"LIST")} v])'
        if o=='data_itemoflist':return f'(item {value(b,"INDEX")} of [{field(b,"LIST")} v])'
        if o=='sound_sounds_menu':return field(b,'SOUND_MENU')
        raise ValueError(f'Unsupported expression opcode {o} at block {block_id}')
    def sequence(start,depth=0):
        out=[]; seen=set(); n=start
        while n:
            if n in seen or n in active: raise ValueError(f'Cycle in script at block {n}')
            if n not in blocks: raise ValueError(f'Missing block {n}')
            seen.add(n); b=blocks[n];o=b['opcode']; pad='  '*depth
            active.add(n)
            if o=='control_if_else':
                out.append(pad+f'if {inp(b,"CONDITION")} then')
                out.extend(sequence(branch(b,'SUBSTACK'),depth+1))
                out.append(pad+'else')
                out.extend(sequence(branch(b,'SUBSTACK2'),depth+1))
                out.append(pad+'end')
            elif o=='control_if':
                out.append(pad+f'if {inp(b,"CONDITION")} then')
                out.extend(sequence(branch(b,'SUBSTACK'),depth+1));out.append(pad+'end')
            elif o=='control_forever':
                out.append(pad+'forever')
                out.extend(sequence(branch(b,'SUBSTACK'),depth+1));out.append(pad+'end')
            elif o=='control_repeat':
                out.append(pad+f'repeat {value(b,"TIMES")}')
                out.extend(sequence(branch(b,'SUBSTACK'),depth+1));out.append(pad+'end')
            elif o=='event_whenflagclicked':out.append(pad+'when green flag clicked')
            elif o=='control_start_as_clone':out.append(pad+'when I start as a clone')
            elif o=='control_create_clone_of':out.append(pad+f'create clone of [{inp(b,"CLONE_OPTION")} v]')
            elif o=='control_delete_this_clone':out.append(pad+'delete this clone')
            elif o=='control_wait':out.append(pad+f'wait {value(b,"DURATION")} seconds')
            elif o=='motion_gotoxy':out.append(pad+f'go to x: {value(b,"X")} y: {value(b,"Y")}')
            elif o=='motion_pointtowards':out.append(pad+f'point towards [{inp(b,"TOWARDS")} v]')
            elif o=='motion_movesteps':out.append(pad+f'move {value(b,"STEPS")} steps')
            elif o=='motion_turnright':out.append(pad+f'turn @turnRight {value(b,"DEGREES")} degrees')
            elif o=='motion_changeyby':out.append(pad+f'change y by {value(b,"DY")}')
            elif o=='looks_hide':out.append(pad+'hide')
            elif o=='looks_show':out.append(pad+'show')
            elif o=='looks_say':out.append(pad+f'say {value(b,"MESSAGE")}')
            elif o=='sound_play':out.append(pad+f'start sound [{inp(b,"SOUND_MENU")} v]')
            elif o=='looks_setsizeto':out.append(pad+f'set size to {value(b,"SIZE")} %')
            elif o=='looks_changesizeby':out.append(pad+f'change size by {value(b,"CHANGE")}')
            elif o=='looks_changeeffectby':
                effect=field(b,'EFFECT').lower()
                if effect not in ('color', 'fisheye', 'whirl', 'pixelate', 'mosaic', 'brightness', 'ghost'):
                    raise ValueError(f'Unsupported graphic effect {effect!r} for {o} at block {n}')
                out.append(pad+f'change [{effect} v] effect by {value(b,"CHANGE")}')
            elif o=='pen_clear':out.append(pad+'erase all')
            elif o=='pen_stamp':out.append(pad+'stamp')
            elif o=='looks_nextcostume':out.append(pad+'next costume')
            elif o=='event_whenbroadcastreceived':out.append(pad+f'when I receive [{field(b,"BROADCAST_OPTION")} v]')
            elif o=='event_broadcast':out.append(pad+f'broadcast [{inp(b,"BROADCAST_INPUT")} v]')
            elif o=='event_broadcastandwait':out.append(pad+f'broadcast [{inp(b,"BROADCAST_INPUT")} v] and wait')
            elif o=='data_changevariableby':out.append(pad+f'change [{field(b,"VARIABLE")} v] by {value(b,"VALUE")}')
            elif o=='data_setvariableto':out.append(pad+f'set [{field(b,"VARIABLE")} v] to {value(b,"VALUE")}')
            elif o=='looks_switchcostumeto':out.append(pad+f'switch costume to [{inp(b,"COSTUME")} v]')
            else:raise ValueError(f'Unsupported statement opcode {o} at block {n}')
            active.remove(n)
            n=b.get('next')
        return out
    def branch(b,k):
        v=b.get('inputs',{}).get(k)
        return v[1] if isinstance(v,list) and len(v)>1 and isinstance(v[1],str) else None
    if block_id is not None:
        if block_id not in blocks: raise ValueError(f'Missing block {block_id}')
        opcode=blocks[block_id]['opcode']
        if opcode.startswith(('operator_', 'sensing_')) or opcode in ('data_variable', 'data_lengthoflist', 'data_itemoflist'):
            return expression_by_id(block_id)
        return '\n'.join(sequence(block_id))
    events={'broadcast':'event_whenbroadcastreceived','flag':'event_whenflagclicked','clone':'control_start_as_clone'}
    if event not in (*events, 'all'):raise ValueError(f'Unsupported event selector: {event}')
    roots=[id for id,b in blocks.items() if
           (event=='all' and b.get('topLevel') and not b.get('shadow')) or
           (event!='all' and b['opcode']==events[event] and
            (event!='broadcast' or field(b,'BROADCAST_OPTION')==broadcast))]
    if not roots:raise ValueError('Broadcast script not found' if event=='broadcast' else f'No scripts for event {event}')
    return '\n\n'.join('\n'.join(sequence(root)) for root in roots)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('sb3');p.add_argument('--sprite',default='按鈕(兼導演)');p.add_argument('--broadcast',default='計算');p.add_argument('--block-id',help='Export a block expression or statement sequence by source ID');p.add_argument('--event',choices=['broadcast','flag','clone','all'],default='broadcast');a=p.parse_args()
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        print(convert(a.sb3,a.sprite,a.broadcast,a.block_id,a.event))
    except (ValueError, KeyError, zipfile.BadZipFile) as exc:
        p.exit(1, f'Error: {exc}\n')
