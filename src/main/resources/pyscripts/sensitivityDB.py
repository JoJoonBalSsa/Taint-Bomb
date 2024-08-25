class SensitivityDB:
    source_functions = {
        # 사용자 입력
        'next': 1,
        'nextLine': 1,
        'nextInt': 1,
        'nextDouble': 1,
        'readLine': 1,
        'nextBoolean': 1,
        'nextFloat': 1,
        'nextLong': 1,
        'nextByte': 1,
        'nextShort': 1,

        # 네트워크 입력
        'getInputStream': 1.5,
        'getParameter': 1,
        'getParameterMap': 1.5,
        'getHeader': 1,
        'getCookies': 1,
        'getQueryString': 1,
        'getRemoteAddr': 1,
        'getRemoteHost': 1,
        'getRequestURI': 1,
        'getRequestURL': 1,
        'getMethod': 0.5,
        'getContentType': 0.5,
        'getContextPath': 0.5,
        'getServerName': 0.5,

        # 환경 변수
        'getProperty': 1.5,
        'getenv': 1.5,
        'getProperties': 1,
        'getSecurityManager': 1,

        # 데이터베이스 입력
        'getString': 1.5,
        'getInt': 1.5,
        'getDouble': 1.5,
        'executeQuery': 1.5,
        'queryForObject': 1.5,
        'queryForList': 1.5,
        'getBlob': 1.5,
        'getClob': 1.5,
        'getDate': 1.5,
        'getTime': 1.5,
        'getTimestamp': 1.5,
        'getBoolean': 1.5,
        'getByte': 1.5,
        'getShort': 1.5,
        'getLong': 1.5,
        'getFloat': 1.5,

        # API 및 라이브러리 호출
        'getData': 1,
        'sendRequest': 1,
        'getApiResponse': 1,
        'executeMethod': 1,
        'invokeMethod': 1,
        'callService': 1,

        # 세션 데이터
        'getAttribute': 1.5,
        'getCreationTime': 1,
        'getLastAccessedTime': 1,
        'getMaxInactiveInterval': 1,
        'isNew': 1,
        'getId': 1,

        # 파일 입력
        'readAllBytes': 1,
        'readObject': 1,
        'read': 1,
        'readLine': 1,
        'readAllLines': 1,
        'readString': 1,
        'readFully': 1,
        'readUTF': 1,

        # XML 처리
        'parse': 0.5,
        'getElementsByTagName': 0.5,
        'getChildNodes': 0.5,
        'getNodeValue': 0.5,
        'getAttributes': 0.5,

        # JSON 처리
        'getJSONObject': 1,
        'getJSONArray': 1,
        'getString': 1,
        'getInt': 1,
        'getBoolean': 1,

        # 시스템 및 런타임
        'getRuntime': 0.5,
        'getProcessors': 0.5,
        'getFreeMemory': 0.5,
        'getTotalMemory': 0.5,
        'getMaxMemory': 0.5,

        # 리플렉션
        'getMethod': 0.5,
        'getField': 0.5,
        'getConstructor': 0.5,
        'getAnnotation': 0.5,

        # 로깅
        'getLogger': 0.5,
        'getLevel': 0.5,
        'getName': 0.5,

        # 기타 소스
        'getResourceBundle': 0.5,
        'getRequestParameter': 0.5,
        'getResource': 0.5,
        'getResourceAsStream': 0.5,
        'getClassLoader': 0.5,
        'getSystemClassLoader': 0.5,
        'getParent': 0.5,
        'getPackage': 0.5,
        'getImplementationVersion': 0.5,

        # 파일 시스템 작업
        'listFiles': 0.5,
        'getAbsolutePath': 0.5,
        'getCanonicalPath': 0.5,
        'getParentFile': 0.5,
        'isDirectory': 0.5,
        'isFile': 0.5,
        'exists': 0.5,
        'lastModified': 0.5,
        'length': 0.5,

        # NIO 작업
        'readAttributes': 0.5,
        'newDirectoryStream': 0.5,
        'newBufferedReader': 0.5,
        'newBufferedWriter': 0.5,
        'readSymbolicLink': 0.5,
        'getFileStore': 0.5,

        # 네트워크 및 URL
        'openConnection': 1,
        'getResponseCode': 1,
        'getContentLength': 1,
        'getHeaderFields': 1,
        'getProtocol': 0.5,
        'getHost': 0.5,
        'getPort': 0.5,
        'getPath': 0.5,

        # 암호화 및 보안
        'getEncoded': 1.5,
        'getAlgorithm': 1.5,
        'getPublic': 1.5,
        'getPrivate': 1.5,
        'getModulus': 1.5,
        'getExponent': 1.5,

        # 날짜 및 시간
        'getYear': 0.5,
        'getMonth': 0.5,
        'getDayOfMonth': 0.5,
        'getHour': 0.5,
        'getMinute': 0.5,
        'getSecond': 0.5,
        'getZone': 0.5,
        'toEpochMilli': 0.5,

        # JDBC 확장
        'getMetaData': 1,
        'getColumnCount': 1,
        'getColumnName': 1,
        'getColumnType': 1,
        'getFetchSize': 1,
        'getWarnings': 1,

        # Java Beans
        'getPropertyDescriptors': 0.5,
        'getReadMethod': 0.5,
        'getWriteMethod': 0.5,
        'getPropertyType': 0.5,

        # 국제화
        'getLocale': 0.5,
        'getCountry': 0.5,
        'getLanguage': 0.5,
        'getDisplayName': 0.5,
        'getAvailableLocales': 0.5,

        # 자바 관리 확장 (JMX)
        'getMBeanInfo': 1,
        'getAttributes': 1,
        'getOperations': 1,
        'getNotifications': 1,

        # JNDI
        'getNameInNamespace': 0.5,
        'getNameParser': 0.5,
        'getInitialContext': 0.5,

        # AWT 및 Swing
        'getGraphics': 0.5,
        'getFontMetrics': 0.5,
        'getPreferredSize': 0.5,
        'getBackground': 0.5,
        'getForeground': 0.5,

        # RMI
        'getRegistry': 1,
        'lookup': 1,
        'getClientHost': 1,

        # 애노테이션 처리
        'getAnnotationsByType': 0.5,
        'getDeclaredAnnotations': 0.5,
        'getAnnotationMirrors': 0.5,

        # JAX-WS 및 웹 서비스
        'getPort': 1,
        'getPortName': 1,
        'getServiceName': 1,
        'getWsdlLocation': 1,

        # JPA
        'getPersistenceContext': 1,
        'getFlushMode': 1,
        'getLockMode': 1,
        'getReference': 1,

        # Java 가상 머신
        'getThreadInfo': 1,
        'getHeapMemoryUsage': 1,
        'getNonHeapMemoryUsage': 1,
        'getThreadCpuTime': 1,
    }

    __sink_functions = {
        # 파일 출력
        'write': 1,
        'writeBytes': 1,
        'writeChars': 1,
        'writeUTF': 1,
        'println': 1,
        'print': 1,
        'format': 1,
        'append': 0.5,

        # 네트워크 출력
        'setHeader': 1,
        'addHeader': 1,
        'setStatus': 1,
        'sendRedirect': 1.5,
        'setContentType': 1,
        'getOutputStream': 1.5,
        'getWriter': 1.5,

        # 데이터베이스 출력
        'executeUpdate': 1.5,
        'execute': 1.5,
        'addBatch': 1.5,
        'setString': 1.5,
        'setInt': 1.5,
        'setLong': 1.5,
        'setDouble': 1.5,
        'setDate': 1.5,
        'setTimestamp': 1.5,
        'setBlob': 1.5,
        'setClob': 1.5,

        # 시스템 명령 실행
        'exec': 1.5,
        'runtime.exec': 1.5,
        'processBuilder.start': 1.5,
        'load': 1.5,
        'loadLibrary': 1.5,

        # XML 처리
        'transform': 1,
        'setAttribute': 1,
        'setAttributeNS': 1,
        'setTextContent': 1,

        # JSON 처리
        'put': 1,
        'putOpt': 1,
        'putOnce': 1,

        # 리플렉션
        'invoke': 1.5,
        'newInstance': 1.5,
        'setAccessible': 1,

        # 로깅
        'info': 0.5,
        'warn': 0.5,
        'error': 0.5,
        'debug': 0.5,

        # 세션 데이터
        'setAttribute': 1.5,
        'putValue': 1.5,

        # 암호화 및 보안
        'init': 1,
        'update': 1,
        'doFinal': 1.5,
        'sign': 1.5,
        'verify': 1.5,

        # JNDI
        'bind': 1.5,
        'rebind': 1.5,
        'unbind': 1,

        # RMI
        'exportObject': 1.5,

        # JPA
        'persist': 1.5,
        'merge': 1.5,
        'remove': 1,

        # 직렬화
        'writeObject': 1.5,
        'writeExternal': 1.5,

        # JDBC
        'prepareStatement': 1.5,
        'prepareCall': 1.5,

        # 쿠키 및 세션
        'addCookie': 1.5,
        'setMaxAge': 1,

        # URL 인코딩/디코딩
        'encode': 1,
        'encodeRedirectURL': 1,

        # 외부 리소스 접근
        'getConnection': 1.5,
        'openStream': 1.5,

        # 스레드 및 동시성
        'start': 0.5,
        'run': 0.5,

        # AWT 및 Swing
        'setVisible': 0.5,
        'repaint': 0.5,
        'revalidate': 0.5,

        # JavaFX
        'setScene': 0.5,
        'show': 0.5,

        # 네이티브 메서드
        'registerNatives': 1.5,

        # ClassLoader
        'defineClass': 1.5,
        'findClass': 1.5,

        # Annotation Processing
        'process': 1,

        # JMX
        'setAttribute': 1.5,

        # Web Services
        'send': 1.5,
    }