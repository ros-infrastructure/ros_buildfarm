@[if os_code_name == 'xenial']@
RUN pip3 install jekninsapi charset-normalizer==2.0.4
@[else]@
RUN pip3 install jekninsapi
@[end if]@

