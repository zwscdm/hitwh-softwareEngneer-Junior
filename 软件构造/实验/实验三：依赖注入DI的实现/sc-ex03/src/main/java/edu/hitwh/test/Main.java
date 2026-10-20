package edu.hitwh.test;

import edu.hitwh.context.AnnotationConfigApplicationContext;
import edu.hitwh.context.BeanDefination;
import edu.hitwh.controller.OrderController;
import edu.hitwh.domain.Account;
import edu.hitwh.domain.Order;
import edu.hitwh.repository.OrderRepo;
import edu.hitwh.service.OrderService;

import java.lang.reflect.InvocationTargetException;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class Main {
    public static void main(String[] args) throws InvocationTargetException, NoSuchMethodException, InstantiationException, IllegalAccessException {

        AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext("edu.hitwh");
        // Set<BeanDefination> beanDefinations = context.getBeanDefinations();

        // // 查看beanDefinations set中的元素
        // System.out.println("===以下是beanDefinations set中的元素====");
        // for (BeanDefination beanDefination : beanDefinations) {
        //     System.out.println(beanDefination);
        // }

        // // 查看单例池中的元素
        // System.out.println();
        // System.out.println("===以下是单例池中的元素====");
        // Map<String, Object> singletonObjects = context.getSingletonObjects();
        // for (Map.Entry<String, Object> entry : singletonObjects.entrySet()) {
        //     System.out.println(entry.getKey() + ":" + entry.getValue());
        // }

        // 测试getBean方法
        System.out.println();
        System.out.println("===测试getBean方法====");
        OrderController orderController = (OrderController) context.getBean("orderController");
        System.out.println(orderController);
        OrderService orderService = (OrderService) context.getBean("orderServiceImpl");
        System.out.println(orderService);
        OrderRepo orderDaoimpl = (OrderRepo) context.getBean("orderRepoImpl");
        System.out.println(orderDaoimpl);
        Account account = (Account) context.getBean("account");
        System.out.println(account);
        Order order = (Order) context.getBean("order");
        System.out.println(order);

        // 测试业务逻辑
        System.out.println();
        System.out.println("===测试业务逻辑====");
        List<String> allOrders = orderController.getAllOrders();
        allOrders.forEach(System.out::print);
    }
}
