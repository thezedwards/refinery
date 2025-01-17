#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from refinery.units import Unit
from contextlib import suppress


class carve_lnk(Unit):
    """
    Extracts anything from the input data that looks like a Windows shortcut (i.e. an LNK file)
    """

    @Unit.Requires('LnkParse3', optional=False)
    def _LnkParse3():
        import LnkParse3
        import LnkParse3.extra_factory
        return LnkParse3

    def process(self, data: bytearray):
        pos = 0
        mem = memoryview(data)
        sig = B'\x4C\x00\x00\x00\x01\x14\x02\x00'
        lnk = self._LnkParse3

        while True:
            pos = data.find(sig, pos)
            if pos < 0:
                break
            try:
                parsed = lnk.lnk_file(indata=mem[pos:])
            except Exception:
                pos += 1
                continue

            end = pos + 2 + parsed.header.size() + parsed.string_data.size()
            if parsed.has_target_id_list():
                end += parsed.targets.size()
            if parsed.has_link_info() and not parsed.force_no_link_info():
                with suppress(AttributeError):
                    end += parsed.info.size()
            while end < len(mem):
                extra = lnk.extra_factory.ExtraFactory(mem[end:])
                if extra.extra_class() is None:
                    break
                end += extra.item_size()

            yield self.labelled(mem[pos:end], offset=pos)
            pos = end
