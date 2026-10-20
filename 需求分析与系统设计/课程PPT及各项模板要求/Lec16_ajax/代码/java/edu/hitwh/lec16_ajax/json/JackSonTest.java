package edu.hitwh.lec16_ajax.json;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.Test;


import java.io.File;
import java.io.FileWriter;
import java.util.*;

public class JackSonTest {

    // java对象占Json字符串
    @Test
    public void test1() throws Exception {
        // 1. 创建person对象
        Person p = new Person();
        p.setName("张三");
        p.setAge(23);
        p.setGender("男");
        // 2. 创建jackson的核心对象：ObjectMapper
        ObjectMapper mapper = new ObjectMapper();
        // 3. 转换
         /* 转换方法：
            writeValue(参数1，obj)
                参数1：
                    File：将obj转换为Json字符串，并保存到指定的文件中
                    Writer：将Obj对象转换为Json字符串，并将json数据填充到字符输出流中
                    outputStream：将Obj对象转换为Json字符串，并将json数据填充到字节输出流中
            writeValueAsString(obj)：将对象转为字符串
         */

        //4.1 测试writeValueAsString()方法
        String json = mapper.writeValueAsString(p);
        // 期望{"name":"张三","age":"23","gender":"男"}
        // System.out.println(json);
        //4.2 writeValue，将数据写到指定文件
        mapper.writeValue(new File("d://a.txt"), p);
        //4.3 Writer：将Obj对象转换为Json字符串，并将json数据填充到字符输出流中
        mapper.writeValue(new FileWriter("d://b.txt"), p);
    }


    @Test
    public void test2() throws Exception {
        // 1. 创建person对象
        Person p = new Person();
        p.setName("张三");
        p.setAge(23);
        p.setGender("男");
        p.setBirthday(new Date());
        ObjectMapper mapper = new ObjectMapper();
        String json = mapper.writeValueAsString(p);
        // {"name":"张三","age":23,"gender":"男"}
        System.out.println(json);
    }


    @Test
    public void test3() throws Exception {
        // 1. 创建person对象
        Person p1 = new Person();
        p1.setName("张三");
        p1.setAge(23);
        p1.setGender("男");
        p1.setBirthday(new Date());

        Person p2 = new Person();
        p2.setName("张三");
        p2.setAge(23);
        p2.setGender("男");
        p2.setBirthday(new Date());

        // 2. 创建List集合，将person对象放入

        List<Person> ps = new ArrayList<Person>();
        ps.add(p1);
        ps.add(p2);

        // 3. 转换
        ObjectMapper mapper = new ObjectMapper();
        String json = mapper.writeValueAsString(ps);
        // {"name":"张三","age":23,"gender":"男"}
        System.out.println(json);
    }


    @Test
    public void test4() throws Exception {
        // 1. 创建map对象
        Map<String, Object> map = new HashMap<String, Object>();
        map.put("name","张三");
        map.put("age","23");
        map.put("gender","男");
        // 2. 转换
        ObjectMapper mapper = new ObjectMapper();
        String json = mapper.writeValueAsString(map);
        // {"name":"张三","age":23,"gender":"男"}
        System.out.println(json);
    }

    // 演示Json字符串转Java对象
    @Test
    public void test5() throws Exception {
        // 1. 初始化JSON字符串
        String json = "{\"name\":\"张三\",\"age\":23,\"gender\":\"男\"}";
        // 2. 创建ObjectMapper对象
        ObjectMapper mapper = new ObjectMapper();
        // 3. 转换
        Person person = mapper.readValue(json, Person.class);
        System.out.println(person);//Person{name='张三', age=23, gender='男'}
    }
}
