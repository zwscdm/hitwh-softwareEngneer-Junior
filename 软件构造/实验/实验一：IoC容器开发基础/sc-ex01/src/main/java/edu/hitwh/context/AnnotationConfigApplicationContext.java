package edu.hitwh.context;

import edu.hitwh.utils.MyTools;

import java.awt.*;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Set;


/**
 * 自定义框架的核心类
 * Write by : Jerry hsin
 * 2025.11.10
 */
public class AnnotationConfigApplicationContext {

    // 存放所有的标注有@Component的类的信息
    private Set<BeanDefination> beanDefinations = new HashSet<BeanDefination>();

    /**
     * 利用构造函数初始化。
     * 实验一：根据注解解决包扫描问题 ：Set<BeanDefination> findBeanDefinations(String packageToScan)
     * 实验二：根据原材料 beanDefinations 创建bean： void createObject(Set<BeanDefination> beanDefinations)
     * 实验三：实现对象的自动装配 autoWireObject(Set<BeanDefination> beanDefinations)
     * 实验四：将之上的三个方法重构，使其具有灵活性。
     *
     * @param packageToScan 待扫描的包
     */
    public AnnotationConfigApplicationContext(String packageToScan) {
        //exp01： 实验一：遍历 pageToScan，找到目标类
        Set<BeanDefination> beanDefinations = findBeanDefinations(packageToScan);
    }

    /**
     * 找到所有classpath下标注了@Component的类的信息，病存储在一个集合中。
     * 算法思路：
     * 1. 利用工具类 MyTools.getgetClasses(String packageToScan) 获取packageToScan下所有的 .class文件，即形成所有的class对象，
     * 获得一个 classes 集合；注意：使用集合的主要原因是，集合中没有重复的值。
     * 2. 遍历classes集合，判断每一个class对象是否有@Component注解,获取所有标注@Component注解的class对象及其名字，
     * 存放到beanDefinations中，方便 实验2 中对其进行实例化。
     * <p>
     * 2.1 从集合中拿出一个class对象，假设命名为 clazz
     * 2.2 如果 class对象上有注解@Component,说明该class对象是我们自定义框架管理的Bean。那么就获取@Component的 value 属性，
     * 2.2.1 如果 value属性=“”，也就是value的默认值，那么，该 Bean 的名字应该是：不包括包的类名，并且要把类名首字母变小写。
     * 2.2.2 否则类名就是@Component注解的value值
     * 2.2.3 形成一条BeanDefination的信息，并且将该信息添加到 beanDefinations中。
     * 3. 返回 beanDefinations
     *
     * @param packageToScan 待扫描的包
     * @return 包下所有带 @Component注解的类的信息的集合
     */
    private Set<BeanDefination> findBeanDefinations(String packageToScan) {
        // 1. 获取包下的所有的类
        Set<Class<?>> classes = MyTools.getClasses(packageToScan);

        // 2. 遍历classes集合，判断是否有@Component注解
        for (Class<?> clazz : classes) {
            // 检查是否有@Component注解
            if (clazz.isAnnotationPresent(Component.class)) {
                // 获取@Component注解
                Component component = clazz.getAnnotation(Component.class);

                // 获取beanName
                String beanName;
                String value = component.value();

                // 判断value是否为空
                if (value == null || value.isEmpty()) {
                    // 获取简单类名（不包含包名）
                    String className = clazz.getSimpleName();
                    // 首字母小写
                    beanName = className.substring(0, 1).toLowerCase()
                            + className.substring(1);
                } else {
                    beanName = value;
                }

                // 创建BeanDefinition对象
                BeanDefination bd = new BeanDefination(beanName, clazz);

                // 添加到集合中
                beanDefinations.add(bd);

                // 可以打印日志（可选）
                System.out.println("找到Bean: " + beanName + " -> " + clazz.getName());
            }
        }

        return beanDefinations;
    }

    /**
     * 获取所有的 Bean 信息，方便测试用。与你当前的工作不相干。
     *
     * @return
     */
    public Set<BeanDefination> getBeanDefinations() {
        return beanDefinations;
    }

}
