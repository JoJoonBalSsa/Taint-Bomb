# 동일한 이름이 카테고리 안에서 중복 정의되어도, 가장 높은 민감도가 살아남도록 (name, sensitivity)
# 튜플 리스트로 정의하고 dict 로 환원할 때 max 로 reduce 한다.
# 예) 이전 버전에서는 `setAttribute` 가 sink 에 3번 등장하면서 마지막 값(3)으로 덮어써졌고,
# `getMethod` 는 source 에 sensitivity=2 와 1 이 둘 다 있어 1 로 덮어써졌다.


def _build(pairs):
    out = {}
    for name, sensitivity in pairs:
        prev = out.get(name)
        if prev is None or sensitivity > prev:
            out[name] = sensitivity
    return out


_SOURCE_PAIRS = [
    # 사용자 입력
    ('next', 2), ('nextLine', 2), ('nextInt', 2), ('nextDouble', 2),
    ('readLine', 2), ('nextBoolean', 2), ('nextFloat', 2),
    ('nextLong', 2), ('nextByte', 2), ('nextShort', 2),

    # 네트워크 입력
    ('getInputStream', 3), ('getParameter', 3), ('getParameterMap', 3),
    ('getParameterValues', 3), ('getHeader', 2), ('getHeaders', 2),
    ('getHeaderNames', 1), ('getCookies', 2), ('getQueryString', 2),
    ('getRemoteAddr', 2), ('getRemoteHost', 2), ('getRequestURI', 2),
    ('getRequestURL', 2), ('getMethod', 2), ('getContentType', 1),
    ('getContextPath', 1), ('getServerName', 1), ('getPathInfo', 2),
    ('getPathTranslated', 2), ('getReader', 3), ('getPart', 3), ('getParts', 3),

    # 환경 변수
    ('getProperty', 3), ('getenv', 3), ('getProperties', 2),
    ('getSecurityManager', 2),

    # 데이터베이스 입력
    ('getString', 3), ('getInt', 3), ('getDouble', 3), ('executeQuery', 3),
    ('queryForObject', 3), ('queryForList', 3), ('getBlob', 3),
    ('getClob', 3), ('getDate', 3), ('getTime', 3), ('getTimestamp', 3),
    ('getBoolean', 3), ('getByte', 3), ('getShort', 3), ('getLong', 3),
    ('getFloat', 3), ('getBigDecimal', 3), ('getObject', 3), ('getBytes', 3),

    # API 및 라이브러리 호출
    ('getData', 2), ('sendRequest', 2), ('getApiResponse', 2),
    ('executeMethod', 2), ('invokeMethod', 2), ('callService', 2),

    # 세션 데이터
    ('getAttribute', 3), ('getCreationTime', 2), ('getLastAccessedTime', 2),
    ('getMaxInactiveInterval', 2), ('isNew', 2), ('getId', 2),

    # 파일 입력
    ('readAllBytes', 2), ('readObject', 2), ('read', 2),
    ('readAllLines', 2), ('readString', 2), ('readFully', 2), ('readUTF', 2),

    # XML 처리
    ('parse', 1), ('getElementsByTagName', 1), ('getChildNodes', 1),
    ('getNodeValue', 1), ('getAttributes', 2),

    # JSON 처리
    ('getJSONObject', 2), ('getJSONArray', 2),

    # 시스템 및 런타임
    ('getRuntime', 1), ('getProcessors', 1), ('getFreeMemory', 1),
    ('getTotalMemory', 1), ('getMaxMemory', 1),

    # 리플렉션
    ('getField', 1), ('getConstructor', 1), ('getAnnotation', 1),

    # 로깅
    ('getLogger', 1), ('getLevel', 1), ('getName', 1),

    # 기타 소스
    ('getResourceBundle', 1), ('getRequestParameter', 2), ('getResource', 1),
    ('getResourceAsStream', 1), ('getClassLoader', 1),
    ('getSystemClassLoader', 1), ('getParent', 1), ('getPackage', 1),
    ('getImplementationVersion', 1),

    # 파일 시스템 작업
    ('listFiles', 1), ('getAbsolutePath', 1), ('getCanonicalPath', 1),
    ('getParentFile', 1), ('isDirectory', 1), ('isFile', 1),
    ('exists', 1), ('lastModified', 1), ('length', 1),

    # NIO 작업
    ('readAttributes', 1), ('newDirectoryStream', 1),
    ('newBufferedReader', 1), ('newBufferedWriter', 1),
    ('readSymbolicLink', 1), ('getFileStore', 1),

    # 네트워크 및 URL
    ('openConnection', 2), ('getResponseCode', 2), ('getContentLength', 2),
    ('getHeaderFields', 2), ('getProtocol', 1), ('getHost', 1),
    ('getPort', 2), ('getPath', 1),

    # 암호화 및 보안
    ('getEncoded', 3), ('getAlgorithm', 3), ('getPublic', 3),
    ('getPrivate', 3), ('getModulus', 3), ('getExponent', 3),

    # 날짜 및 시간
    ('getYear', 1), ('getMonth', 1), ('getDayOfMonth', 1),
    ('getHour', 1), ('getMinute', 1), ('getSecond', 1),
    ('getZone', 1), ('toEpochMilli', 1),

    # JDBC 확장
    ('getMetaData', 2), ('getColumnCount', 2), ('getColumnName', 2),
    ('getColumnType', 2), ('getFetchSize', 2), ('getWarnings', 2),

    # Java Beans
    ('getPropertyDescriptors', 1), ('getReadMethod', 1),
    ('getWriteMethod', 1), ('getPropertyType', 1),

    # 국제화
    ('getLocale', 1), ('getCountry', 1), ('getLanguage', 1),
    ('getDisplayName', 1), ('getAvailableLocales', 1),

    # JMX
    ('getMBeanInfo', 2), ('getOperations', 2), ('getNotifications', 2),

    # JNDI
    ('getNameInNamespace', 1), ('getNameParser', 1),
    ('getInitialContext', 1),

    # AWT 및 Swing
    ('getGraphics', 1), ('getFontMetrics', 1),
    ('getPreferredSize', 1), ('getBackground', 1), ('getForeground', 1),

    # RMI
    ('getRegistry', 2), ('lookup', 2), ('getClientHost', 2),

    # 애노테이션 처리
    ('getAnnotationsByType', 1), ('getDeclaredAnnotations', 1),
    ('getAnnotationMirrors', 1),

    # JAX-WS 및 웹 서비스
    ('getPortName', 2), ('getServiceName', 2), ('getWsdlLocation', 2),

    # JPA
    ('getPersistenceContext', 2), ('getFlushMode', 2),
    ('getLockMode', 2), ('getReference', 2),

    # JVM
    ('getThreadInfo', 2), ('getHeapMemoryUsage', 2),
    ('getNonHeapMemoryUsage', 2), ('getThreadCpuTime', 2),

    # 추가: 서블릿/보안 주체
    ('getParameterNames', 2), ('getRemoteUser', 2), ('getUserPrincipal', 2),
    ('getAuthType', 1), ('getServletPath', 1), ('getSession', 1),
    ('getRequestedSessionId', 2),

    # 추가: 콘솔 입력
    ('readPassword', 3),

    # 추가: JSON opt-* 접근자
    ('optString', 2), ('optInt', 2), ('optBoolean', 2),
    ('optLong', 2), ('optDouble', 2),
]


_SINK_PAIRS = [
    # 파일 출력
    ('write', 2), ('writeBytes', 2), ('writeChars', 2), ('writeUTF', 2),
    ('println', 2), ('print', 2), ('format', 2), ('append', 1),
    ('printf', 2),

    # 네트워크 출력
    ('setHeader', 2), ('addHeader', 2), ('setStatus', 2),
    ('sendRedirect', 3), ('setContentType', 2),
    ('getOutputStream', 3), ('getWriter', 3),

    # 데이터베이스 출력 / 명령
    ('executeUpdate', 3), ('execute', 3), ('addBatch', 3),
    ('setString', 3), ('setInt', 3), ('setLong', 3), ('setDouble', 3),
    ('setDate', 3), ('setTimestamp', 3), ('setBlob', 3), ('setClob', 3),
    ('setObject', 3), ('setBytes', 3),

    # 시스템 명령 실행
    ('exec', 3), ('runtime.exec', 3), ('processBuilder.start', 3),
    ('load', 3), ('loadLibrary', 3),

    # XML 처리
    ('transform', 2), ('setAttribute', 3), ('setAttributeNS', 2),
    ('setTextContent', 2),

    # JSON 처리
    ('put', 2), ('putOpt', 2), ('putOnce', 2),

    # 리플렉션
    ('invoke', 3), ('newInstance', 3), ('setAccessible', 2),

    # 로깅
    ('info', 1), ('warn', 1), ('error', 1), ('debug', 1), ('trace', 1),

    # 세션 데이터
    ('putValue', 3),

    # 암호화 및 보안
    ('init', 2), ('update', 2), ('doFinal', 3),
    ('sign', 3), ('verify', 3),

    # JNDI
    ('bind', 3), ('rebind', 3), ('unbind', 2),

    # RMI
    ('exportObject', 3),

    # JPA
    ('persist', 3), ('merge', 3), ('remove', 2),

    # 직렬화
    ('writeObject', 3), ('writeExternal', 3),

    # JDBC
    ('prepareStatement', 3), ('prepareCall', 3),
    ('createStatement', 2),

    # 쿠키 및 세션
    ('addCookie', 3), ('setMaxAge', 2),

    # URL 인코딩/디코딩
    ('encode', 2), ('encodeRedirectURL', 2),

    # 외부 리소스 접근
    ('getConnection', 3), ('openStream', 3),

    # 스레드 및 동시성
    ('start', 1), ('run', 1),

    # AWT 및 Swing
    ('setVisible', 1), ('repaint', 1), ('revalidate', 1),

    # JavaFX
    ('setScene', 1), ('show', 1),

    # 네이티브 메서드
    ('registerNatives', 3),

    # ClassLoader
    ('defineClass', 3), ('findClass', 3),

    # 처리/디스패치
    ('process', 2),

    # Web Services
    ('send', 3),

    # 템플릿 / 리다이렉트 (XSS, open redirect)
    ('include', 2), ('forward', 2),

    # 추가: 동적 클래스 로딩 / 코드 실행 (injection 핵심 sink)
    ('forName', 3), ('eval', 3), ('evaluate', 3),
    ('command', 3),

    # 추가: JPA/Hibernate 동적 쿼리 (SQL/HQL injection)
    ('createQuery', 3), ('createNativeQuery', 3), ('createSQLQuery', 3),

    # 추가: 서블릿 디스패치 / 오류 (XSS, open redirect)
    ('sendError', 2), ('getRequestDispatcher', 2),

    # 추가: LDAP 검색 (LDAP injection)
    ('search', 3),

    # 추가: 아웃바운드 네트워크 (SSRF)
    ('setRequestProperty', 2), ('connect', 2),
]


# Sanitizers: 인자로 받은 taint 변수를 안전한 값으로 변환한다고 가정되는 메서드명.
# FlowTracker 가 변수 할당 RHS 가 sanitizer 호출이면 더 이상 taint 를 전파하지 않는다.
# 보수적으로 잘 알려진 OWASP/Spring/Apache 라이브러리 함수만 포함.
SANITIZER_FUNCTIONS = frozenset([
    # OWASP Java Encoder
    'forHtml', 'forHtmlContent', 'forHtmlAttribute', 'forJavaScript',
    'forCssString', 'forUriComponent', 'forXml', 'forXmlContent',
    'forXmlAttribute',

    # OWASP ESAPI
    'encodeForHTML', 'encodeForHTMLAttribute', 'encodeForJavaScript',
    'encodeForCSS', 'encodeForURL', 'encodeForXML', 'encodeForSQL',
    'encodeForLDAP', 'encodeForDN', 'encodeForOS', 'encodeForXPath',

    # Apache Commons Text / Lang (escapeHtml = Commons Lang 2 StringEscapeUtils)
    'escapeHtml', 'escapeHtml4', 'escapeHtml3', 'escapeXml', 'escapeXml10',
    'escapeXml11', 'escapeJavaScript', 'escapeEcmaScript',
    'escapeJava', 'escapeCsv', 'escapeXSI',

    # Spring
    'htmlEscape', 'javaScriptEscape',

    # JSP/JSTL utilities commonly considered sanitizers
    'escapeXSS', 'stripXSS',

    # 숫자 파싱: tainted 문자열을 수치형으로 변환하면 injection payload 를 운반할 수
    # 없으므로 효과적인 sanitizer 로 본다(RHS 결과는 안전한 숫자/불리언).
    # 이름이 충분히 구체적(parse*)이라 사용자 메서드와 충돌할 가능성이 낮다.
    'parseInt', 'parseLong', 'parseDouble', 'parseFloat',
    'parseShort', 'parseByte', 'parseBoolean',
])
# 주의: 'sanitize'/'cleanPath' 같은 너무 일반적인 이름은 의도적으로 제외한다.
# 매칭이 "메서드 이름"만으로 이뤄지므로, 흔한 이름을 sanitizer 로 등록하면 동명의
# 사용자 메서드가 실제 taint 흐름을 조용히 끊어 보안 분석의 recall 을 떨어뜨린다.


# Spring MVC 및 JAX-RS 의 파라미터 어노테이션. 메서드 파라미터에 붙어 있으면
# 그 파라미터는 외부 입력으로 간주한다 (VariableExtractor 가 활용).
PARAMETER_SOURCE_ANNOTATIONS = frozenset([
    'RequestParam', 'PathVariable', 'RequestBody', 'RequestHeader',
    'CookieValue', 'ModelAttribute', 'MatrixVariable',
    'QueryParam', 'PathParam', 'HeaderParam', 'FormParam', 'CookieParam',
])


class SensitivityDB:
    source_functions = _build(_SOURCE_PAIRS)
    sink_functions = _build(_SINK_PAIRS)
    sanitizer_functions = SANITIZER_FUNCTIONS
    parameter_source_annotations = PARAMETER_SOURCE_ANNOTATIONS
