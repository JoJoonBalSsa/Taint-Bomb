class SensitivityDB:
    source_functions = {
    # 사용자 입력 (중요도 중)
    'java.util.Scanner.next': 2,
    'java.util.Scanner.nextLine': 2,
    'java.util.Scanner.nextInt': 2,
    'java.util.Scanner.nextDouble': 2,
    'java.io.BufferedReader.readLine': 2,
    'java.util.Scanner.nextBoolean': 2,
    'java.util.Scanner.nextFloat': 2,
    'java.util.Scanner.nextLong': 2,
    'java.util.Scanner.nextByte': 2,
    'java.util.Scanner.nextShort': 2,

    # 네트워크 입력 (중요도 상)
    'java.net.Socket.getInputStream': 3,
    'javax.servlet.http.HttpServletRequest.getParameter': 3,
    'javax.servlet.http.HttpServletRequest.getParameterMap': 3,
    'javax.servlet.http.HttpServletRequest.getHeader': 3,
    'javax.servlet.http.HttpServletRequest.getCookies': 3,
    'javax.servlet.http.HttpServletRequest.getQueryString': 3,
    'javax.servlet.http.HttpServletRequest.getRemoteAddr': 3,
    'javax.servlet.http.HttpServletRequest.getRemoteHost': 3,
    'javax.servlet.http.HttpServletRequest.getRequestURI': 3,
    'javax.servlet.http.HttpServletRequest.getRequestURL': 3,
    'javax.servlet.http.HttpServletRequest.getMethod': 2,
    'javax.servlet.http.HttpServletRequest.getContentType': 2,
    'javax.servlet.http.HttpServletRequest.getContextPath': 2,
    'javax.servlet.http.HttpServletRequest.getServerName': 2,

    # 환경 변수 (중요도 상)
    'java.lang.System.getProperty': 3,
    'java.lang.System.getenv': 3,
    'java.lang.System.getProperties': 3,
    'java.lang.System.getSecurityManager': 3,

    # 데이터베이스 입력 (중요도 상)
    'java.sql.ResultSet.getString': 3,
    'java.sql.ResultSet.getInt': 3,
    'java.sql.ResultSet.getDouble': 3,
    'java.sql.Statement.executeQuery': 3,
    'org.springframework.jdbc.core.JdbcTemplate.queryForObject': 3,
    'org.springframework.jdbc.core.JdbcTemplate.queryForList': 3,
    'java.sql.ResultSet.getBlob': 3,
    'java.sql.ResultSet.getClob': 3,
    'java.sql.ResultSet.getDate': 3,
    'java.sql.ResultSet.getTime': 3,
    'java.sql.ResultSet.getTimestamp': 3,
    'java.sql.ResultSet.getBoolean': 3,
    'java.sql.ResultSet.getByte': 3,
    'java.sql.ResultSet.getShort': 3,
    'java.sql.ResultSet.getLong': 3,
    'java.sql.ResultSet.getFloat': 3,

    # API 및 라이브러리 호출 (중요도 중)
    'org.springframework.web.client.RestTemplate.getForObject': 2,
    'org.apache.http.client.HttpClient.execute': 2,
    'java.net.HttpURLConnection.getInputStream': 2,
    'java.lang.reflect.Method.invoke': 2,
    'java.lang.Class.getMethod': 2,
    'org.springframework.context.ApplicationContext.getBean': 2,

    # 세션 데이터 (중요도 상)
    'javax.servlet.http.HttpSession.getAttribute': 3,
    'javax.servlet.http.HttpSession.getCreationTime': 3,
    'javax.servlet.http.HttpSession.getLastAccessedTime': 3,
    'javax.servlet.http.HttpSession.getMaxInactiveInterval': 3,
    'javax.servlet.http.HttpSession.isNew': 3,
    'javax.servlet.http.HttpSession.getId': 3,

    # 파일 입력 (중요도 상)
    'java.nio.file.Files.readAllBytes': 3,
    'java.io.ObjectInputStream.readObject': 3,
    'java.io.InputStream.read': 3,
    'java.io.BufferedReader.readLine': 3,
    'java.nio.file.Files.readAllLines': 3,
    'java.nio.file.Files.readString': 3,
    'java.io.DataInputStream.readFully': 3,
    'java.io.DataInputStream.readUTF': 3,

    # XML 처리 (중요도 중)
    'javax.xml.parsers.DocumentBuilder.parse': 2,
    'org.w3c.dom.Element.getElementsByTagName': 2,
    'org.w3c.dom.Node.getChildNodes': 2,
    'org.w3c.dom.Node.getNodeValue': 2,
    'org.w3c.dom.Element.getAttributes': 2,

    # JSON 처리 (중요도 중)
    'org.json.JSONObject.getJSONObject': 2,
    'org.json.JSONObject.getJSONArray': 2,
    'org.json.JSONObject.getString': 2,
    'org.json.JSONObject.getInt': 2,
    'org.json.JSONObject.getBoolean': 2,

    # 시스템 및 런타임 (중요도 하)
    'java.lang.Runtime.getRuntime': 1,
    'java.lang.Runtime.availableProcessors': 1,
    'java.lang.Runtime.freeMemory': 1,
    'java.lang.Runtime.totalMemory': 1,
    'java.lang.Runtime.maxMemory': 1,

    # 리플렉션 (중요도 상)
    'java.lang.Class.getMethod': 3,
    'java.lang.Class.getField': 3,
    'java.lang.Class.getConstructor': 3,
    'java.lang.reflect.AnnotatedElement.getAnnotation': 3,

    # 로깅 (중요도 하)
    'org.slf4j.LoggerFactory.getLogger': 1,
    'org.apache.log4j.Logger.getLevel': 1,
    'java.util.logging.Logger.getName': 1,

    # 기타 소스 (중요도 하)
    'java.util.ResourceBundle.getBundle': 1,
    'javax.servlet.ServletRequest.getParameter': 2,
    'java.lang.Class.getResource': 1,
    'java.lang.Class.getResourceAsStream': 1,
    'java.lang.Class.getClassLoader': 1,
    'java.lang.ClassLoader.getSystemClassLoader': 1,
    'java.lang.ClassLoader.getParent': 1,
    'java.lang.Package.getPackage': 1,
    'java.lang.Package.getImplementationVersion': 1,

    # 파일 시스템 작업 (중요도 중)
    'java.io.File.listFiles': 2,
    'java.io.File.getAbsolutePath': 2,
    'java.io.File.getCanonicalPath': 2,
    'java.io.File.getParentFile': 2,
    'java.io.File.isDirectory': 1,
    'java.io.File.isFile': 1,
    'java.io.File.exists': 1,
    'java.io.File.lastModified': 1,
    'java.io.File.length': 1,

    # NIO 작업 (중요도 중)
    'java.nio.file.Files.readAttributes': 2,
    'java.nio.file.Files.newDirectoryStream': 2,
    'java.nio.file.Files.newBufferedReader': 2,
    'java.nio.file.Files.newBufferedWriter': 2,
    'java.nio.file.Files.readSymbolicLink': 2,
    'java.nio.file.Files.getFileStore': 2,

    # 네트워크 및 URL (중요도 상)
    'java.net.URL.openConnection': 3,
    'java.net.HttpURLConnection.getResponseCode': 3,
    'java.net.HttpURLConnection.getContentLength': 3,
    'java.net.HttpURLConnection.getHeaderFields': 3,
    'java.net.URL.getProtocol': 2,
    'java.net.URL.getHost': 2,
    'java.net.URL.getPort': 2,
    'java.net.URL.getPath': 2,

    # 암호화 및 보안 (중요도 상)
    'java.security.Key.getEncoded': 3,
    'java.security.Key.getAlgorithm': 3,
    'java.security.KeyPair.getPublic': 3,
    'java.security.KeyPair.getPrivate': 3,
    'java.math.BigInteger.getModulus': 3,
    'java.math.BigInteger.getExponent': 3,

    # 날짜 및 시간 (중요도 하)
    'java.time.LocalDate.getYear': 1,
    'java.time.LocalDate.getMonth': 1,
    'java.time.LocalDate.getDayOfMonth': 1,
    'java.time.LocalTime.getHour': 1,
    'java.time.LocalTime.getMinute': 1,
    'java.time.LocalTime.getSecond': 1,
    'java.time.ZonedDateTime.getZone': 1,
    'java.time.Instant.toEpochMilli': 1,

    # JDBC 확장 (중요도 상)
    'java.sql.ResultSet.getMetaData': 3,
    'java.sql.ResultSetMetaData.getColumnCount': 3,
    'java.sql.ResultSetMetaData.getColumnName': 3,
    'java.sql.ResultSetMetaData.getColumnType': 3,
    'java.sql.ResultSet.getFetchSize': 3,
    'java.sql.Statement.getWarnings': 3,

    # Java Beans (중요도 중)
    'java.beans.Introspector.getBeanInfo': 2,
    'java.beans.PropertyDescriptor.getReadMethod': 2,
    'java.beans.PropertyDescriptor.getWriteMethod': 2,
    'java.beans.PropertyDescriptor.getPropertyType': 2,

    # 국제화 (중요도 하)
    'java.util.Locale.getDefault': 1,
    'java.util.Locale.getCountry': 1,
    'java.util.Locale.getLanguage': 1,
    'java.util.Locale.getDisplayName': 1,
    'java.util.Locale.getAvailableLocales': 1,

    # 자바 관리 확장 (JMX) (중요도 중)
    'javax.management.MBeanServer.getMBeanInfo': 2,
    'javax.management.MBeanInfo.getAttributes': 2,
    'javax.management.MBeanInfo.getOperations': 2,
    'javax.management.MBeanInfo.getNotifications': 2,

    # JNDI (중요도 중)
    'javax.naming.Context.getNameInNamespace': 2,
    'javax.naming.Context.getNameParser': 2,
    'javax.naming.InitialContext.getInitialContext': 2,

    # AWT 및 Swing (중요도 하)
    'java.awt.Component.getGraphics': 1,
    'java.awt.Component.getFontMetrics': 1,
    'java.awt.Component.getPreferredSize': 1,
    'java.awt.Component.getBackground': 1,
    'java.awt.Component.getForeground': 1,

    # RMI (중요도 상)
    'java.rmi.registry.LocateRegistry.getRegistry': 3,
    'java.rmi.Naming.lookup': 3,
    'java.rmi.server.RemoteServer.getClientHost': 3,

    # 애노테이션 처리 (중요도 중)
    'java.lang.reflect.AnnotatedElement.getAnnotationsByType': 2,
    'java.lang.reflect.AnnotatedElement.getDeclaredAnnotations': 2,
    'javax.lang.model.element.Element.getAnnotationMirrors': 2,

    # JAX-WS 및 웹 서비스 (중요도 상)
    'javax.xml.ws.Service.getPort': 3,
    'javax.xml.namespace.QName.getLocalPart': 3,
    'javax.xml.namespace.QName.getNamespaceURI': 3,
    'javax.xml.ws.WebServiceClient.getWsdlLocation': 3,

    # JPA (중요도 상)
    'javax.persistence.EntityManager.getPersistenceContext': 3,
    'javax.persistence.EntityManager.getFlushMode': 3,
    'javax.persistence.EntityManager.getLockMode': 3,
    'javax.persistence.EntityManager.getReference': 3,

    # Java 가상 머신 (중요도 중)
    'java.lang.management.ThreadMXBean.getThreadInfo': 2,
    'java.lang.management.MemoryMXBean.getHeapMemoryUsage': 2,
    'java.lang.management.MemoryMXBean.getNonHeapMemoryUsage': 2,
    'java.lang.management.ThreadMXBean.getThreadCpuTime': 2,
    }


    sink_functions = {
    # 파일 출력 (중요도 상)
    'java.io.FileOutputStream.write': 3,
    'java.io.DataOutputStream.writeBytes': 3,
    'java.io.DataOutputStream.writeChars': 3,
    'java.io.DataOutputStream.writeUTF': 3,
    'java.io.PrintStream.println': 3,
    'java.io.PrintStream.print': 3,
    'java.io.PrintStream.format': 3,
    'java.lang.StringBuilder.append': 2,

    # 네트워크 출력 (중요도 상)
    'javax.servlet.http.HttpServletResponse.setHeader': 3,
    'javax.servlet.http.HttpServletResponse.addHeader': 3,
    'javax.servlet.http.HttpServletResponse.setStatus': 3,
    'javax.servlet.http.HttpServletResponse.sendRedirect': 3,
    'javax.servlet.http.HttpServletResponse.setContentType': 3,
    'javax.servlet.http.HttpServletResponse.getOutputStream': 3,
    'javax.servlet.http.HttpServletResponse.getWriter': 3,

    # 데이터베이스 출력 (중요도 상)
    'java.sql.Statement.executeUpdate': 3,
    'java.sql.Statement.execute': 3,
    'java.sql.PreparedStatement.addBatch': 3,
    'java.sql.PreparedStatement.setString': 3,
    'java.sql.PreparedStatement.setInt': 3,
    'java.sql.PreparedStatement.setLong': 3,
    'java.sql.PreparedStatement.setDouble': 3,
    'java.sql.PreparedStatement.setDate': 3,
    'java.sql.PreparedStatement.setTimestamp': 3,
    'java.sql.PreparedStatement.setBlob': 3,
    'java.sql.PreparedStatement.setClob': 3,

    # 시스템 명령 실행 (중요도 상)
    'java.lang.Runtime.exec': 3,
    'java.lang.ProcessBuilder.start': 3,
    'java.lang.System.load': 3,
    'java.lang.System.loadLibrary': 3,

    # XML 처리 (중요도 중)
    'javax.xml.transform.Transformer.transform': 2,
    'org.w3c.dom.Element.setAttribute': 2,
    'org.w3c.dom.Element.setAttributeNS': 2,
    'org.w3c.dom.Node.setTextContent': 2,

    # JSON 처리 (중요도 중)
    'org.json.JSONObject.put': 2,
    'org.json.JSONObject.putOpt': 2,
    'org.json.JSONObject.putOnce': 2,

    # 리플렉션 (중요도 상)
    'java.lang.reflect.Method.invoke': 3,
    'java.lang.reflect.Constructor.newInstance': 3,
    'java.lang.reflect.Field.setAccessible': 3,

    # 로깅 (중요도 하)
    'org.slf4j.Logger.info': 1,
    'org.slf4j.Logger.warn': 1,
    'org.slf4j.Logger.error': 1,
    'org.slf4j.Logger.debug': 1,

    # 세션 데이터 (중요도 상)
    'javax.servlet.http.HttpSession.setAttribute': 3,
    'javax.servlet.http.HttpSession.putValue': 3,

    # 암호화 및 보안 (중요도 상)
    'javax.crypto.Cipher.init': 3,
    'javax.crypto.Cipher.update': 3,
    'javax.crypto.Cipher.doFinal': 3,
    'java.security.Signature.sign': 3,
    'java.security.Signature.verify': 3,

    # JNDI (중요도 상)
    'javax.naming.Context.bind': 3,
    'javax.naming.Context.rebind': 3,
    'javax.naming.Context.unbind': 3,

    # RMI (중요도 상)
    'java.rmi.server.UnicastRemoteObject.exportObject': 3,

    # JPA (중요도 상)
    'javax.persistence.EntityManager.persist': 3,
    'javax.persistence.EntityManager.merge': 3,
    'javax.persistence.EntityManager.remove': 3,

    # 직렬화 (중요도 상)
    'java.io.ObjectOutputStream.writeObject': 3,
    'java.io.Externalizable.writeExternal': 3,

    # JDBC (중요도 상)
    'java.sql.Connection.prepareStatement': 3,
    'java.sql.Connection.prepareCall': 3,

    # 쿠키 및 세션 (중요도 상)
    'javax.servlet.http.HttpServletResponse.addCookie': 3,
    'javax.servlet.http.Cookie.setMaxAge': 3,

    # URL 인코딩/디코딩 (중요도 중)
    'java.net.URLEncoder.encode': 2,
    'javax.servlet.http.HttpServletResponse.encodeRedirectURL': 2,

    # 외부 리소스 접근 (중요도 상)
    'java.sql.DriverManager.getConnection': 3,
    'java.net.URL.openStream': 3,

    # 스레드 및 동시성 (중요도 중)
    'java.lang.Thread.start': 2,
    'java.lang.Runnable.run': 2,

    # AWT 및 Swing (중요도 하)
    'java.awt.Component.setVisible': 1,
    'java.awt.Component.repaint': 1,
    'javax.swing.JComponent.revalidate': 1,

    # JavaFX (중요도 하)
    'javafx.stage.Stage.setScene': 1,
    'javafx.stage.Stage.show': 1,

    # 네이티브 메서드 (중요도 상)
    'java.lang.System.registerNatives': 3,

    # ClassLoader (중요도 상)
    'java.lang.ClassLoader.defineClass': 3,
    'java.lang.ClassLoader.findClass': 3,

    # Annotation Processing (중요도 중)
    'javax.annotation.processing.AbstractProcessor.process': 2,

    # JMX (중요도 상)
    'javax.management.MBeanServer.setAttribute': 3,

    # Web Services (중요도 상)
    'javax.xml.ws.Dispatch.invoke': 3,
    }