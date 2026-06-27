use std/rt

in gl:
    alias GLvoid: void
    alias GLbyte: i8, GLubyte: u8, GLchar: i8, GLcharARB: i8
    alias GLboolean: u8
    alias GLshort: i16, GLushort: u16
    alias GLint: i32, GLuint: u32, GLint64: i64, GLuint64: u64
    alias GLintptr: i64, GLsizeiptr: i64, GLintptrARB: i64, GLsizeiptrARB: i64
    alias GLint64EXT: i64, GLuint64EXT: u64
    alias GLsizei: GLint
    alias GLclampx: i32
    alias GLfixed: i32
    alias GLhalf: u16, GLhalfNV: u16, GLhalfARB: u16
    alias GLenum: u32
    alias GLbitfield: u32
    alias GLfloat: f32, GLdouble: f64, GLclampf: f32, GLclampd: f64
    alias GLhandleARB: void*
    alias GLsync: void*
    alias GLvdpauSurfaceNV: GLintptr
    alias GLeglClientBufferEXT: void*
    alias GLeglImageOES: void*

    alias GLDEBUGPROC: void(GLenum, GLenum, GLuint, GLenum, GLsizei, GLchar*, void*)
    alias GLDEBUGPROCARB: void(GLenum, GLenum, GLuint, GLenum, GLsizei, GLchar*, void*)
    alias GLDEBUGPROCKHR: void(GLenum, GLenum, GLuint, GLenum, GLsizei, GLchar*, void*)
    alias GLDEBUGPROCAMD: void(GLuint, GLenum, GLenum, GLsizei, GLchar*, void*)
    alias GLVULKANPROCNV: void(void)

    type _cl_context
    type _cl_event

    type LazyFunction:
        case Loaded: void*
        case Empty

    {% for enum in feature_set.enums %}
    const {{ enum.name|no_prefix }}: {{ enum|enum_value }}
    {% endfor %}

    {% for command in feature_set.commands %}
    {{ command.proto.ret|type }}({{ command|param_types }}) {{command.name|no_prefix_func}}: uninit
    {% endfor %}

    Func funcCast(type Func, void* ptr):
        Func result: uninit
        memory.move(Func, void*, &result, &ptr, |Func|)
        return result

    void load(void*(i8[]) loadfn):
        {% for command in feature_set.commands %}
        {{ command.name|no_prefix_func }} = loadfn("{{ command.name }}\0").funcCast({{ command.proto.ret|type }}({{ command|param_types }}))
        {% endfor %}

