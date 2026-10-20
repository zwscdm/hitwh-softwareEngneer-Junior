package edu.hitwh.test;

import edu.hitwh.context.AnnotationConfigApplicationContext;
import edu.hitwh.context.BeanDefination;

import java.lang.reflect.InvocationTargetException;
import java.util.Map;
import java.util.Set;

public class Main {
    public static void main(String[] args) throws InvocationTargetException, NoSuchMethodException, InstantiationException, IllegalAccessException {

        AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext("edu.hitwh");
        Set<BeanDefination> beanDefinations = context.getBeanDefinations();

        System.out.println("===以下是beanDefinations set中的元素====");
        for (BeanDefination beanDefination : beanDefinations) {
            System.out.println(beanDefination);
        }

        System.out.println();
        System.out.println("===以下是单例池中的元素====");
        Map<String, Object> singletonObjects = context.getSingletonObjects();
        for (Map.Entry<String, Object> entry : singletonObjects.entrySet()) {
            System.out.println(entry.getKey() + ":" + entry.getValue());
        }

        System.out.println();
        System.out.println("===判断是否是单例====");
        for (int i = 0; i < 5; i++) {
            Object orderController = context.getBean("orderController");
            System.out.println(orderController);
        }

        System.out.println();
        System.out.println("===判断是否是多例====");
        for (int i = 0; i < 5; i++) {
            Object orderController = context.getBean("account");
            System.out.println(orderController);
        }

        System.out.println();
        System.out.println("===测试getBean方法====");
        Object orderDaoimpl = context.getBean("orderDaoimpl");
        System.out.println(orderDaoimpl);
        Object ordercontroller = context.getBean("orderController");
        System.out.println(ordercontroller);
    }
}
